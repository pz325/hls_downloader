import m3u8
import urllib
import os
import argparse


def chdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    old_cwd = os.getcwd()
    os.chdir(path)
    return old_cwd


def downloadStream1():
    '''
    download http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8
    to bipbop_4x3
    '''
    host = 'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/'
    master_playlist_file = 'bipbop_4x3_variant.m3u8'
    local_root = 'bipbop_4x3'
    print('downloading {uri} to {local}'.format(uri=host+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    # master_playlist_uri = host + master_playlist_file

    # print('saving {master_playlist_uri} as {master_playlist_file}'.format(master_playlist_uri=master_playlist_uri, master_playlist_file=master_playlist_file))
    # urllib.urlretrieve(master_playlist_uri, master_playlist_file)

    # print('loading {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    # master_playlist = m3u8.load(master_playlist_uri)

    # for playlist in master_playlist.playlists:
    #     subfolder, stream_playlist_file = playlist.uri.split('/')
    #     if not os.path.exists(subfolder):
    #         os.makedirs(subfolder)
    #     stream_playlist_uri = host + playlist.uri
    #     print('saving {stream_playlist_uri} as {stream_playlist_file}'.format(stream_playlist_uri=stream_playlist_uri, stream_playlist_file=playlist.uri))
    #     urllib.urlretrieve(stream_playlist_uri, stream_playlist_file)
    #     if not os.path.exists(os.path.join(subfolder, stream_playlist_file)):
    #         os.rename(stream_playlist_file, os.path.join(subfolder, stream_playlist_file))

    #     print('loading {stream_playlist_uri}'.format(stream_playlist_uri=stream_playlist_uri))
    #     stream_playlist = m3u8.load(stream_playlist_uri)

    #     for segment in stream_playlist.segments:
    #         segment_uri = host + subfolder + '/' + segment.uri
    #         print('saving {segment_uri} as {segment_file}'.format(segment_uri=segment_uri, segment_file=subfolder+'/'+segment.uri))
    #         urllib.urlretrieve(segment_uri, segment.uri)
    #         if not os.path.exists(os.path.join(subfolder, segment.uri)):
    #             os.rename(segment.uri, os.path.join(subfolder, segment.uri))

    os.chdir(old_cwd)


def downloadStream2():
    '''
    download http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8
    to bipbop_16x9
    '''
    host = 'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/'
    master_playlist_file = 'bipbop_16x9_variant.m3u8'
    local_root = 'bipbop_16x9'
    print('downloading {uri} to {local}'.format(uri=host+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    os.chdir(old_cwd)


def downloadStream3():
    '''
    download https://tungsten.applimg.com/VOD/bipbop_adv_example_v2/master.m3u8
    to bipbop_adv_example_v2
    '''
    host = 'https://tungsten.applimg.com/VOD/bipbop_adv_example_v2'
    master_playlist_file = 'master.m3u8'
    local_root = 'bipbop_adv_example_v2'
    print('downloading {uri} to {local}'.format(uri=host+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    os.chdir(old_cwd)

    pass


def downloadStream4():
    pass


def main():
    parser = argparse.ArgumentParser(description='Download Apple reference HLS streams')
    parser.add_argument('--index', type=int, choices=range(0, 3), help='Index of streams to download')
    args = parser.parse_args()

    tasks = [downloadStream1, downloadStream2, downloadStream3]
    if args.index:
        tasks[args.index]()
    else:
        for task in tasks:
            task()


if __name__ == '__main__':
    main()
