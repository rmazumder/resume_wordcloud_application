# HR Resume analyser using word cloud
Its is a HR application view resume in wordcloud images


Technology stack used:




AWS LAMBDA : pyhton function to text extraction and wordcloud image genearation
S3 Bucket for static hosting of the hrml files
dynamoDB to store the textual data for processing
UI :  aws-sdk for javascript  and angular js for UI


application pipeline : 

   1) UI upload the pdf to S3 bucket under "resune" 
   2) Lambda S3 events kicks in and calls lambda function
   3) lambda function process the file (pdf, doc,docx,rtf, images) to extract text and created wordcloud image. Finally pushes the images to another folder(images) in S3 bucket and adds dynamo db entry with all relevent data.
   4) UI page load list all the images for S3 bucekt and data from dynamo db to render UI display.

Module used in python :
	 wordclud - for generating wordcloud
	 boto3 - for S3 and dynamo db connection
	 pdfminer - for pdf text extraction
	 antiword - for doc extraction
	 tessaract - for OCR
   	 docx - for docs
         unrtf - for rtf text extraction

The python dependency are created in two seperate layer 
	1) tesseract -- containing tessaract, antiword and unrtf
	2) wordcloud -- wordcloud, pdfminer

	The following links are good resource for python dependency build for aws lambda layer
	https://github.com/gwittchen/lambda-ocr
	https://github.com/bweigel/aws-lambda-tesseract-layer

UI module : aws-sdk for javascript , angularjs_1 and bootstrap 4

Build and deployment : serverless is used for build, packaging and deployment



BUILD and Deployment instruction:

lambda function :

