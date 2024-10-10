"""SFTP Helper"""

# Authors: Warith Harchaoui <warith.harchaoui@deraison.ai>

from hashlib import new
import json
import pysftp


import os_helper


def credentials(config_path: str) -> dict:
    """sftp_credentials function gets SFTP credentials from file or folder path

    Args:
        config_path (str): File or folder config path

    Returns:
        dict: Credentials Dictionary
    """
    keys = ['sftp_host', "sftp_login", "sftp_passwd",
            "sftp_destination_path", "sftp_https"]  # mandatory keys
    sftp_cred = os_helper.get_config(
        config_path, keys=keys, config_type="SFTP")
    return sftp_cred


def get_client_sftp(cred: dict):
    """get_client_sftp returns an SFTP client based on the SFTP credentials.
    This is just a 'with' wrapper over the used pysftp toolbox

    Example:
    $ local_path = 'file.txt'
    $ remote_path = 'sftp://sftp.server/file.txt'
    $ new_local_path = 'new_file.txt'
    $ with get_client_sftp(cred) as sftp:
    $     sftp.put(local, remote_path) # upload
    $     sftp.get(remote_path, new_local_path) # download
    $     sftp.remove(remote_path) # remote deletion

    Args:
        cred (dict): Credentials Dictionary for establishing a connection

    Returns:
        res: an SFTP client to be used within the 'with' paradigm
    """
    try:
    # if True:
        cnopts = pysftp.CnOpts()
        cnopts.hostkeys = None
        client = pysftp.Connection(
            cred["sftp_host"], username=cred["sftp_login"], cnopts=cnopts, password=cred["sftp_passwd"])
        return client
    except:
        msg = 'Try on your terminal:\nsftp sftp://%s@%s\nonce' % (
            cred["sftp_login"], cred['sftp_host'])
        os_helper.check(
            False, msg='Sftp client does not work:\n%s' % (msg))


def strip_sftp_path(sftp_address: str, cred: dict) -> str:
    """strip_sftp_path strips sftp path

    Example:
    sftp://host/folder/file -> /folder/file

    Args:
        sftp_address (str): sftp path
        cred (dict): SFTP credentials dictionary

    Returns:
        str: stripped ftp path
    """
    return sftp_address.replace('sftp://', '').replace(cred["sftp_host"], '')


def remote_file_exists(sftp_address: str, cred: dict) -> bool:
    """remote_file_exists boolean function for existing remote SFTP file

    Args:
        sftp_address (str): sftp path
        cred (dict): SFTP credentials dictionary

    Returns:
        bool: whether the remote file exists or not
    """
    p = strip_sftp_path(sftp_address, cred)
    res = False
    try:
        with get_client_sftp(cred) as sftp:
            res = sftp.exists(p)
            os_helper.info(
                'sftp file %s existence checked: %s' % (sftp_address, 'True' if res else 'False'))
    except:
        pass
    if not(res):
        os_helper.info(
            'sftp file %s does not exist' % sftp_address)
    else:
        os_helper.info('sftp file exists')
    return res


def delete(sftp_address: str, cred: dict, check_exists=False) -> bool:
    """delete function removes a remote an SFTP file and returns True for success

    Args:
        sftp_address (str): sftp path to be removed
        cred (dict): SFTP credentials dictionary

    Returns:
        bool: True for successful deletion (including when the file was already deleted)
    """
    remote_exists = remote_file_exists(sftp_address, cred)
    if check_exists and not(remote_exists):
        os_helper.info(
            'sftp remote file %s does not exist, so there is no need to remove it' % sftp_address, error_code=True)
    if not(remote_exists):
        return True
    p = strip_sftp_path(sftp_address, cred)
    try:
        with get_client_sftp(cred) as sftp:
            sftp.remove(p)
            os_helper.check(not(remote_file_exists(sftp_address, cred)),
                            msg='sftp remote file %s is not removed inspite of your removal attempt' % sftp_address)
            os_helper.info('sftp successful removal of %s' %
                           (p))
            return True
    except IOError as err:
        os_helper.info(err)
    os_helper.info('sftp failed removal of %s' %
                   (p), error=True)
    return False


def upload(local_path: str, cred: dict, sftp_address: str = "") -> str:
    """upload function uploads a local file to remote sftp path

    Args:
        local_path (str): origin local file
        cred (dict): SFTP credentials dictionary
        sftp_address (str): destination remote file, if empty ("") it is a random file name with the right extension. Defaults to ""

    Returns:
        str: Remote remote path if successful and None otherwise
    """
    remote_path = sftp_address
    if os_helper.emptystring(remote_path):
        _, _, ext = os_helper.folder_name_ext(local_path)
        h = os_helper.hashfile(local_path, hash_content=True, date=True)
        remote_path = '%s/%s.%s' % (cred["sftp_destination_path"], h, ext)

    delete(remote_path, cred)
    p = strip_sftp_path(remote_path, cred)
    try:
        with get_client_sftp(cred) as sftp:
            sftp.put(local_path, p, preserve_mtime=True, confirm=True)
            os_helper.check(remote_file_exists(remote_path, cred),
                            msg='File %s is not uploaded inspite of your upload attempt' % remote_path)
            os_helper.info('sftp upload successful from %s to %s' %
                           (local_path, p))
            return remote_path
    except (IOError, OSError) as err:
        os_helper.info(err)
    os_helper.info('sftp upload failed from %s to %s' %
                   (local_path, p), error=True)
    return None


def download(sftp_address: str, cred: dict, local_path: str = "") -> str:
    """upload function uploads a remote sftp file to local file


    Args:
        sftp_address (str): origin remote file
        cred (dict): SFTP credentials dictionary
        local_path (str): destination local file

    Returns:
        str: Remote local path if successful and None otherwise
    """
    p = strip_sftp_path(sftp_address, cred)
    download_path = local_path
    if os_helper.emptystring(download_path):
        download_path = p.split('/')[-1]
    try:
        with get_client_sftp(cred) as sftp:
            sftp.get(p, download_path, preserve_mtime=True)
        os_helper.checkfile(download_path, msg='sftp download failed')
        os_helper.info('sftp download successful from %s to %s' %
                       (p, download_path))
        return download_path
    except (IOError, OSError) as err:
        os_helper.info(err)
    os_helper.info('sftp download failed from %s to %s' %
                   (p, local_path), error=True)
    return None


if __name__ == "__main__":
    verbosity = 3
    verbose = verbosity > 0
    os_helper.verbosity(verbosity)
    
    os_helper.info("Loading FTP credientials")
    config_path = "config/sftp"
    credentials = credentials(config_path)

    folder = "sftp_test"
    os_helper.make_directory(folder)

    local_file = "original.txt"
    local_file = os_helper.os_path_constructor([folder, local_file])

    new_file = "downloaded.txt"
    new_file = os_helper.os_path_constructor([folder, new_file])

    new_file_2 = "downloaded_2.txt"
    new_file_2 = os_helper.os_path_constructor([folder, new_file_2])
    
    os_helper.remove_files([local_file, new_file, new_file_2])
    
    remote_file = credentials["sftp_destination_path"] + '/tt.txt'

    os_helper.info("Remote file %s existence check" %   remote_file)

    os_helper.info("Creating local file")
    with os_helper.open(local_file, 'wt') as fout:
        msg = os_helper.now_string()
        msg = '%s\nSFTP Test File' % msg
        fout.write(msg)

    u = upload(local_file, credentials, remote_file)
    os_helper.check(not(u is None), msg='Upload of %s to %s failed' %
                    (local_file, u))
    os_helper.info("Successful upload of %s to %s" %
                   (local_file, u))

    b = remote_file_exists(remote_file, credentials)
    os_helper.check(
        b, msg='Remote file %s has not been uploaded (remote_file_exists failed)' % remote_file)
    os_helper.info("Remote file %s exists" %
                   (remote_file))

    d = download(u, credentials, new_file)
    os_helper.check(not(d is None), msg='Download of %s to %s failed' %
                    (u, d))
    os_helper.info("Successful download of %s to %s" %
                   (u, d))

    u = upload(local_file, credentials)
    url = u.replace(credentials["sftp_destination_path"],
                    '').strip().strip('/').strip()
    url = '%s/%s' % (credentials["sftp_https"].strip().strip('/').strip(), url)
    os_helper.check(not(u is None), msg='Upload of %s to %s failed' %
                    (local_file, u))
    os_helper.info("Successful upload of %s to %s" %
                   (local_file, u))
    os_helper.info("Check url:\n%s" %
                   (url))

    d = download(u, credentials, new_file_2)
    os_helper.check(not(d is None), msg='Download of %s to %s failed' %
                    (u, d))
    os_helper.info("Successful download of %s to %s" %
                   (u, d))
