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


def download_uri(uri, local, clear_local=False):
    '''
    Download resource from uri, save to local, i.e. path/to/target.file (relative to CWD)

    @param uri Full URI of the target
    @param local path/to/target.file
    '''
    print('downloading {uri} to {local}'.format(uri=uri, local=local))
    if os.path.exists(local):
        if clear_local:
            os.remove(local)
        else:
            print('{local} exists'.format(local=local))
            return

    target_name = os.path.basename(local)
    subfolder = os.path.dirname(local)
    if subfolder and not os.path.exists(subfolder):
        os.makedirs(subfolder)

    download(uri, target_name)
    os.rename(target_name, local)


def download_master_playlist(master_playlist_uri):
    '''
    @param master_playlist_uri Full URI of master playlist
    '''
    host, subpath, filename = parse_uri(master_playlist_uri)
    download_uri(master_playlist_uri, filename, clear_local=True)  # always refresh playlist - so the script can be used for parsing live streams
    print('loading {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    with open(filename, 'r') as f:
        content = f.read()
    master_playlist = m3u8.loads(content)
    return master_playlist


def is_full_uri(uri):
    return uri.startswith('http://') or uri.startswith('https://')


def download_stream(uri, subpath=None):
    '''
    @param uri
    @param subpath Relative subpath, if None, use uri's subpath
    '''
    stream_playlist_host, stream_playlist_subpath, stream_playlist_filename = parse_uri(uri)
    local_stream_playlist_filename = os.path.join(stream_playlist_subpath, stream_playlist_filename)
    if subpath:
        local_stream_playlist_filename = os.path.join(subpath, stream_playlist_filename)
    download_uri(uri, local_stream_playlist_filename, clear_local=True)   # always refresh playlist - so the script can be used for parsing live streams

    print('loading {local}'.format(local=local_stream_playlist_filename))
    with open(local_stream_playlist_filename, 'r') as f:
        content = f.read()
    stream_playlist = m3u8.loads(content)

    for segment in stream_playlist.segments:
        if segment.uri.startswith('#'):
            continue
        if is_full_uri(segment.uri):
            segment_host, segment_subpath, segment_filename = parse_uri(segment.uri)
            download_uri(segment.uri, os.path.join(segment_subpath, segment_filename))
        else:
            segment_uri = stream_playlist_host + '/' + stream_playlist_subpath + '/' + segment.uri
            download_uri(segment_uri, os.path.join(subpath, segment.uri))
        if segment.byterange:
            break


def parse_uri(uri):
    '''
    parse URI into host_root, subpath, filename

    e.g. http://example.com/path/to/stream_id/index.m3u8
        host_root = http://example.com
        subpath = path/to/stream_id
        filename = index.m3u8

    @param uri
    @return host_root, subpath, filename
    '''
    print('parsing {uri}'.format(uri=uri))
    url = urlparse(uri)
    host_root = url.scheme + '://' + url.netloc
    subpath = os.path.dirname(url.path)[1:]
    filename = os.path.basename(url.path)

    return host_root, subpath, filename


def download_hls_stream(master_playlist_uri, id='.'):
    '''
    Download hls stream to local folder indiciated by id
    @param master_playlist_uri
    @param id Defaut CWD
    '''
    print('master_playlist_uri: {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    local_root = id

    print('downloading {uri} to {local}'.format(uri=master_playlist_uri, local=local_root))
    old_cwd = chdir(local_root)

    master_playlist = download_master_playlist(master_playlist_uri)

    host_root, subpath, master_playlist_file = parse_uri(master_playlist_uri)
    # download resource from stream playlist
    for playlist in master_playlist.playlists:
        if is_full_uri(playlist.uri):
            download_stream(playlist.uri)
        else:
            playlist_uri = host_root + '/' + subpath + '/' + playlist.uri
            download_stream(playlist_uri, os.path.dirname(playlist.uri))

    # download resource from URI
    pattern = 'URI="(.*)"'
    for l in open(master_playlist_file):
        m = re.search(pattern, l)
        if m:
            uri = m.group(1)
            if is_full_uri(uri):
                download_stream(uri)
            else:
                playlist_uri = host_root + '/' + subpath + '/' + uri
                download_stream(playlist_uri, os.path.dirname(uri))

    os.chdir(old_cwd)


def main():

    # root, subpath, filename = parse_uri('http://devimages.apple.com.edgekey.net/bipbop_4x3_variant.m3u8')
    # print(root, subpath, filename)

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
