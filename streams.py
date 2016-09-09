import m3u8
import os
import argparse
import re
import requests
from urlparse import urlparse


def chdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    old_cwd = os.getcwd()
    os.chdir(path)
    print('current working directory: {cwd}'.format(cwd=path))
    return old_cwd


def download(uri, filename):
    '''
    download from uri and save as filename (relative to CWD)
    @param uri
    @param filename
    '''
    resp = requests.get(uri, verify=False)
    with open(filename, 'wb') as f:
        f.write(resp.content)


def download_uri(host_root, subpath, clear_local=False):
    '''
    Download resource from host_root+subpath
    save to subpath, i.e. path/to/target.file (relative to CWD)

    @param subpath path/to/target.file
    '''
    print('downloading {uri} to {local}'.format(uri=host_root+subpath, local=subpath))
    if os.path.exists(subpath):
        if clear_local:
            os.remove(subpath)
        else:
            print('{subpath} exists'.format(subpath=subpath))
            return

    target_name = os.path.basename(subpath)
    subfolder = os.path.dirname(subpath)
    if subfolder and not os.path.exists(subfolder):
        os.makedirs(subfolder)

    download(host_root+subpath, target_name)
    os.rename(target_name, subpath)


def download_master_playlist(host_root, master_playlist_file):
    '''
    @param host_root
    @param master_playlist+file
    '''
    master_playlist_uri = host_root + master_playlist_file
    download_uri(host_root, master_playlist_file)
    print('loading {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    with open(master_playlist_file, 'r') as f:
        content = f.read()
    master_playlist = m3u8.loads(content)
    return master_playlist


def download_stream(host_root, stream_playlist_file):
    print('host_root: {host_root}'.format(host_root=host_root))
    print('stream_playlist_file: {stream_playlist_file}'.format(stream_playlist_file=stream_playlist_file))
    download_uri(host_root, stream_playlist_file)
    stream_playlist_uri = host_root + stream_playlist_file
    print('loading {stream_playlist_uri}'.format(stream_playlist_uri=stream_playlist_uri))
    with open(stream_playlist_file, 'r') as f:
        content = f.read()
    stream_playlist = m3u8.loads(content)

    subpath = os.path.basename(stream_playlist_file)
    for segment in stream_playlist.segments:
        download_uri(host_root, '/'.join([subpath, segment.uri]))
        if segment.byterange:
            break


def parse_uri(uri):
    '''
    parse URI into host_root, filename
    e.g. http://example.com/path/to/stream_id/index.m3u8
    host_root = http://example.com/path/to/stream_id/
    filename = index.m3u8
    @param uri
    @return host_root, filename
    '''
    url = urlparse(uri)
    host_root = url.scheme + '://' + url.netloc + os.path.dirname(url.path) + '/'
    filename = os.path.basename(url.path)
    return host_root, filename


def download_hls_stream(master_playlist_uri, id='.'):
    '''
    Download hls stream to local folder indiciated by id
    @param master_playlist_uri
    @param id Defaut CWD
    '''
    print('master_playlist_uri: {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    host_root, master_playlist_file, local_root = parse_uri(master_playlist_uri)

    print('downloading {uri} to {local}'.format(uri=host_root+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    master_playlist = download_master_playlist(host_root, master_playlist_file)

    # download resource from stream playlist
    for playlist in master_playlist.playlists:
        download_stream(host_root, playlist.uri)

    # download resource from URI
    pattern = 'URI="(.*)"'
    for l in open(master_playlist_file):
        m = re.search(pattern, l)
        if m:
            uri = m.group(1)
            download_stream(host_root, uri)

    os.chdir(old_cwd)


def main():
    parser = argparse.ArgumentParser(description='Download HLS streams -- default to download Apple reference HLS streams')
    parser.add_argument('--stream', help='master playlist URI, m3u8 resource')
    parser.add_argument('--id', help='stream id. Used a subfolder name for the downloads')
    args = parser.parse_args()

    if args.stream:
        download_hls_stream(args.stream, args.id)
    else:
        download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8', 'bipbop_4x3')
        download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8', 'bipbop_16x9')
        download_hls_stream('http://tungsten.aaplimg.com/VOD/bipbop_adv_example_v2/master.m3u8', 'bipbop_adv_example_v2')


if __name__ == '__main__':
    main()
