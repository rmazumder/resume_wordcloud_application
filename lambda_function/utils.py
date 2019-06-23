import subprocess


def get_subprocess_output(cmdline, redirect_stderr=True, display_output_on_exception=True, logger=None, **kwargs):
    if redirect_stderr: kwargs['stderr'] = subprocess.STDOUT
    print("sub process")
    try:
        output = subprocess.check_output(cmdline, **kwargs)
        return output
    except: 
        raise

    return ''
#end def


