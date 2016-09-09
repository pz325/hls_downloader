import m3u8
import urllib
import os
import argparse


def chdir(path):
    if not os.path.exists(path):
        os.makedirs(path)
    old_cwd = os.getcwd()
    os.chdir(path)
    print('current working directory: {cwd}'.format(cwd=path))
    return old_cwd


def downloadUri(host_root, subpath, clear_local=False):
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

    urllib.urlretrieve(host_root+subpath, target_name)
    os.rename(target_name, subpath)


def downloadStream1():
    '''
    download http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/bipbop_4x3_variant.m3u8
    to bipbop_4x3
    '''
    host_root = 'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_4x3/'
    master_playlist_file = 'bipbop_4x3_variant.m3u8'
    local_root = 'bipbop_4x3'
    print('downloading {uri} to {local}'.format(uri=host_root+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    master_playlist_uri = host_root + master_playlist_file
    downloadUri(host_root, master_playlist_file)

    print('loading {master_playlist_uri}'.format(master_playlist_uri=master_playlist_uri))
    master_playlist = m3u8.load(master_playlist_uri)

    for playlist in master_playlist.playlists:
        downloadUri(host_root, playlist.uri)
        stream_playlist_uri = host_root + playlist.uri
        print('loading {stream_playlist_uri}'.format(stream_playlist_uri=stream_playlist_uri))
        stream_playlist = m3u8.load(stream_playlist_uri)

        subpath, _ = playlist.uri.split('/')
        for segment in stream_playlist.segments:
            downloadUri(host_root, os.path.join(subpath, segment.uri))

    os.chdir(old_cwd)


def downloadStream2():
    '''
    download http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/bipbop_16x9_variant.m3u8
    to bipbop_16x9
    '''
    host_root = 'http://devimages.apple.com.edgekey.net/streaming/examples/bipbop_16x9/'
    master_playlist_file = 'bipbop_16x9_variant.m3u8'
    local_root = 'bipbop_16x9'
    print('downloading {uri} to {local}'.format(uri=host_root+master_playlist_file, local=local_root))
    old_cwd = chdir(local_root)

    os.chdir(old_cwd)


def downloadStream3():
    '''
    download https://tungsten.applimg.com/VOD/bipbop_adv_example_v2/master.m3u8
    to bipbop_adv_example_v2
    '''
    host_root = 'https://tungsten.applimg.com/VOD/bipbop_adv_example_v2'
    master_playlist_file = 'master.m3u8'
    local_root = 'bipbop_adv_example_v2'
    print('downloading {uri} to {local}'.format(uri=host_root+master_playlist_file, local=local_root))
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
