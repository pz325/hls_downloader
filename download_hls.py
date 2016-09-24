import m3u8
import os
import argparse
import re
import downloader
import util


def download_master_playlist(master_playlist_uri):
    '''
    @param master_playlist_uri Full URI of master playlist
    '''
    host, subpath, filename = util.parse_uri(master_playlist_uri)
    downloader.download_uri(master_playlist_uri, filename, clear_local=True)  # always refresh playlist - so the script can be used for parsing live streams
    print('loading {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    with open(filename, 'r') as f:
        content = f.read()
    master_playlist = m3u8.loads(content)
    return master_playlist


def download_stream(uri, subpath=None):
    '''
    @param uri
    @param subpath Relative subpath, if None, use uri's subpath
    '''
    stream_playlist_host, stream_playlist_subpath, stream_playlist_filename = util.parse_uri(uri)
    local_stream_playlist_filename = os.path.join(stream_playlist_subpath, stream_playlist_filename)
    if subpath:
        local_stream_playlist_filename = os.path.join(subpath, stream_playlist_filename)
    downloader.download_uri(uri, local_stream_playlist_filename, clear_local=True)   # always refresh playlist - so the script can be used for parsing live streams

    print('loading {local}'.format(local=local_stream_playlist_filename))
    with open(local_stream_playlist_filename, 'r') as f:
        content = f.read()
    stream_playlist = m3u8.loads(content)
    print('{num_segments} segments to download in {stream_playlist}'.format(num_segments=len(stream_playlist.segments), stream_playlist=uri))
    for segment in stream_playlist.segments:
        if segment.uri.startswith('#'):
            continue
        if util.is_full_uri(segment.uri):
            segment_host, segment_subpath, segment_filename = parse_uri(segment.uri)
            downloader.download_uri_async(segment.uri, os.path.join(segment_subpath, segment_filename))
        else:
            segment_uri = stream_playlist_host + '/' + stream_playlist_subpath + '/' + segment.uri
            downloader.download_uri_async(segment_uri, os.path.join(subpath, segment.uri))
        if segment.byterange:
            break


def download_hls_stream(master_playlist_uri, id='.', num_workers=10):
    '''
    Download hls stream to local folder indiciated by id
    @param master_playlist_uri
    @param id Defaut CWD
    '''
    print('master_playlist_uri: {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    local_root = id

    print('downloading {uri} to {local}'.format(uri=master_playlist_uri, local=local_root))
    old_cwd = util.chdir(local_root)

    downloader.start(num_workers)

    master_playlist = download_master_playlist(master_playlist_uri)

    host_root, subpath, master_playlist_file = util.parse_uri(master_playlist_uri)
    # download resource from stream playlist
    for playlist in master_playlist.playlists:
        if util.is_full_uri(playlist.uri):
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
            if util.is_full_uri(uri):
                download_stream(uri)
            else:
                playlist_uri = host_root + '/' + subpath + '/' + uri
                download_stream(playlist_uri, os.path.dirname(uri))

    downloader.stop()
    os.chdir(old_cwd)


def main():
    parser = argparse.ArgumentParser(description='Download HLS streams -- default to download Apple reference HLS streams')
    parser.add_argument('--stream', help='master playlist URI, m3u8 resource')
    parser.add_argument('--id', help='stream id. Used a subfolder name for the downloads')
    parser.add_argument('--workers', default=10, help='Number of download workers')
    args = parser.parse_args()

    if args.stream:
        download_hls_stream(args.stream, args.id, args.workers)
    else:
        download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8', 'bipbop_4x3')
        # download_hls_stream('http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8', 'bipbop_16x9')
        # download_hls_stream('http://tungsten.aaplimg.com/VOD/bipbop_adv_example_v2/master.m3u8', 'bipbop_adv_example_v2')


if __name__ == '__main__':
    main()
