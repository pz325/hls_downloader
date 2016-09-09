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

    paths = subpath.split('/')
    target_name = paths[-1]
    del paths[-1]
    if paths:
        subfolder = '/'.join(paths)
        if not os.path.exists(subfolder):
            os.makedirs(subfolder)

    download(host_root+subpath, target_name)
    os.rename(target_name, os.path.join(subfolder, target_name))


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

    subpath = stream_playlist_file.split('/')
    del subpath[-1]
    subpath = '/'.join(subpath)

    for segment in stream_playlist.segments:
        download_uri(host_root, '/'.join([subpath, segment.uri]))
        if segment.byterange:
            break





def downloadStream4():
    pass


def parse_uri(uri):
    '''
    parse URI into host_root, filename, and stream_id
    e.g. http://example.com/path/to/stream_id/index.m3u8
    host_root = http://example.com/path/to/stream_id/
    filename = index.m3u8
    stream_id = stream_id
    @param uri
    @return host_root, filename, stream_id
    '''
    url = urlparse(uri)
    host_root = url.scheme + '://' + url.netloc + os.path.dirname(url.path) + '/'
    filename = os.path.basename(url.path)
    local_root = os.path.split(os.path.dirname(url.path))[1]
    if not local_root:
        local_root = '.'
    return host_root, filename, local_root


def download_hls_stream(master_playlist_uri):
    print('master_playlist_uri: {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    host_root, master_playlist_file, local_root = parse_uri(master_playlist_uri)

    print('downloading {uri} to {local}'.format(uri=host_root+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    master_playlist = download_master_playlist(host_root, master_playlist_file)
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
    # download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8')
    # download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8')
    download_hls_stream('http://tungsten.aaplimg.com/VOD/bipbop_adv_example_v2/master.m3u8')
    # parser = argparse.ArgumentParser(description='Download Apple reference HLS streams')
    # parser.add_argument('--index', type=int, choices=range(0, 3), help='Index of streams to download')
    # args = parser.parse_args()

    # tasks = [download_stream1, download_stream2, download_stream3]
    # if args.index is not None:
    #     tasks[args.index]()
    # else:
    #     for task in tasks:
    #         task()


if __name__ == '__main__':
    main()
