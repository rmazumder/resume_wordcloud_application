from datetime import datetime, time
import io
import json
import os
import re
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile
from zipfile import is_zipfile, ZipFile
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
import boto3
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
import pytesseract
import PIL.Image
import sys, getopt
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from urllib.parse import unquote_plus

from utils import get_subprocess_output

LAMBDA_TASK_ROOT = os.environ.get('LAMBDA_TASK_ROOT', os.path.dirname(os.path.abspath(__file__)))
BIN_DIR = os.path.join("/opt", 'bin')
LIB_DIR = os.path.join("/opt", 'lib')




with NamedTemporaryFile(mode='w', delete=False) as f:
    CATDOCRC_PATH = f.name
    f.write('charset_path = {}\n'.format(os.path.join(LIB_DIR, 'catdoc', 'charsets')))
    f.write('map_path = {}\n'.format(os.path.join(LIB_DIR, 'catdoc', 'charsets')))
#end with





def _get_subprocess_output(*args, **kwargs):
    return get_subprocess_output(*args, **kwargs)
#end def


def pdf_to_text(document_path, event, context):
    print("insidepdf")
    pagenums = set()
    output = io.StringIO()
    manager = PDFResourceManager()
    converter = TextConverter(manager, output, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    infile = open(document_path, 'rb')
    for page in PDFPage.get_pages(infile, pagenums):
        interpreter.process_page(page)
    infile.close()
    converter.close()
    text = output.getvalue()
    output.close
    return text
#end def



def doc_to_text(document_path, event, context):
    global logger
    cmdline = [os.path.join(BIN_DIR, 'antiword'), '-t', '-w', '0', '-m', 'UTF-8', document_path]

    try:
        text = _get_subprocess_output(cmdline, display_output_on_exception=False, shell=False, env=dict(ANTIWORDHOME=os.path.join(LIB_DIR, 'antiword')))
        text = text.decode('utf-8', errors='ignore').strip()
    except CalledProcessError as e:
        print(e)
        if b'Rich Text Format' in e.output:
            return rtf_to_text(document_path, event, context)

        elif b'"docx" file' in e.output or is_zipfile(document_path):
            return docx_to_text(document_path, event, context)

        else:
            text = None
        #end if
    #end try

    if text is None:  # Fallback to catdoc
        cmdline = [os.path.join(BIN_DIR, 'catdoc'), '-a', document_path]
        text = _get_subprocess_output(cmdline, shell=False, env=dict(CATDOCRC_PATH=CATDOCRC_PATH))
        text = text.decode('utf-8', errors='ignore').strip()
    #end if

    return text
#end def




def docx_to_text(document_path, event, context):
    global logger
    print("before import")

    print("after import")
    try:
        doc = Document(document_path)
        doc_body = doc.element.body
        blocks = []
        for child in doc_body.iterchildren():
            if isinstance(child, CT_P): blocks.append(Paragraph(child, doc_body).text)
            elif isinstance(child, CT_Tbl): blocks.append('\n'.join(' | '.join(cell.text for cell in row.cells) for row in Table(child, doc_body).rows))
        #end for

        text = '\n\n'.join(blocks).strip()

        return text

    except Exception:
        print("Exception")
    #end try

    # Extract it from the XML
    with ZipFile(document_path) as document_zipfile:
        xml_content = document_zipfile.read('word/document.xml')

    try: from xml.etree.cElementTree import XML
    except ImportError: from xml.etree.ElementTree import XML

    tree = XML(xml_content)

    DOCX_NAMESPACE = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
    DOCX_PARA = DOCX_NAMESPACE + 'p'
    DOCX_TEXT = DOCX_NAMESPACE + 't'

    paragraphs = []
    for paragraph in tree.getiterator(DOCX_PARA):
        texts = [node.text for node in paragraph.getiterator(DOCX_TEXT) if node.text]
        if texts:
            paragraphs.append(''.join(texts))
    #end for

    text = '\n\n'.join(paragraphs)

    return text
#end def

def img_to_text(document_path, event, context):
    os.environ['TESSDATA_PREFIX'] = "/opt/data/tessdata"
    text = pytesseract.image_to_string(Image.open(document_path), config='--psm 6')
    return text


def rtf_to_text(document_path, event, context):
    cmdline = [os.path.join(BIN_DIR, 'unrtf'), '-P', os.path.join(LIB_DIR, 'unrtf'), '--text', document_path]
    text = _get_subprocess_output(cmdline, shell=False)
    text = text.decode('utf-8', errors='ignore')

    new_lines = []
    in_header = True
    for line in text.split('\n'):
        if in_header and line.startswith('###'): continue
        else:
            new_lines.append(line)
            in_header = False
        #end if
    #end for
    text = '\n'.join(new_lines).strip()
    text = re.sub(r'[\x0e-\x1f]', '', text)

    return text
#end def

PARSE_FUNCS = {
    '.doc': doc_to_text,
    '.docx': docx_to_text,
    '.dot': doc_to_text,
    '.pdf': pdf_to_text,
    '.rtf': rtf_to_text,
    '.png': img_to_text,
    '.jpg': img_to_text,
    '.jpeg': img_to_text

}

def extractEmail(text):
    regexEmail = '\S+@\S+'
    emails = re.findall(regexEmail, text)
    return emails


def extractPhoneNumber(text):
    regexPhone = r'^\D*(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$'
    phones = re.findall(regexPhone, text)
    return phones

def handle(event, context):
    global logger
    s3 = boto3.resource('s3')
    bucket =event['Records'][0]['s3']['bucket']['name']
    key =event['Records'][0]['s3']['object']['key']
    key = unquote_plus(key)
    print("New file : {} uploaded in bucket: {} ".format(key, bucket))
    tmpfile = '/tmp/'+key[7:];
    s3.meta.client.download_file(bucket, key, tmpfile)
    print('I am done downloading the file in tmp folder ' + tmpfile)
    _, ext = os.path.splitext(tmpfile)  # get format from extension
    ext = ext.lower()
    extract_func = PARSE_FUNCS.get(ext)
    print("Extraction function identified as")
    print(extract_func)
    if extract_func is None:
        print("No function identified. Unsupported file type")
    #end if

    textractor_results = {}
    try:
        text = extract_func(tmpfile, event, context)
        textractor_results = dict(method=extract_func.__name__, size=len(text), success=True)
        if len(text) == 0: print('<{}> does not contain any content.'.format(tmpfile))
        #end if
        print("text extracted successfully now generating wordcloud image")
        stoptextfile = LAMBDA_TASK_ROOT+"/stop-words.txt"
        stopwords = set(STOPWORDS)
        new_words =open(stoptextfile).read().split()
        new_stopwords=stopwords.union(new_words)
        wordcloud = WordCloud(max_font_size=50,  stopwords = new_stopwords, background_color="white").generate(text)
        plt.figure()
        plt.imshow(wordcloud, interpolation="bilinear")
        plt.axis("off")
        imageFile= key+".png"
        imageFile = imageFile[7:]
        wordcloud.to_file("/tmp/"+imageFile)
        print("Wordcloud file created {}".format(imageFile))
        data = open('/tmp/'+imageFile, 'rb')
        imageFile = "image/"+imageFile
        s3.Bucket(bucket).put_object(ACL='public-read',Key=imageFile, Body=data)
        print("WordCloud image uploaded succesfully " + imageFile)
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table('resumewordcloudTable')
        print(table)
        wordclouddata =  wordcloud.words_
        for k, v in wordclouddata.items():
            wordclouddata[k] = str(v)
        email = ''.join(extractEmail(text))
        phone = ''.join(extractPhoneNumber(text))

        table.put_item(Item= {'name':key,'resumekey': key,'resumetext': wordclouddata  , 'imagekey': imageFile, 'email':"-"+email, 'phone':'-'+phone})
        print("data updated in dynamo table")

    except Exception as e:
        print('Extraction exception {} for <{}>'.format(tmpfile, e))

#end def
