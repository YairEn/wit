# Upload 174

from datetime import datetime, timezone
import filecmp
import logging
import os
from pathlib import Path
import random
import shutil
import sys

from graphviz import Digraph

INIT = 'init'
ADD = 'add'
COMMIT = 'commit'
STATUS = 'status'
CHECKOUT = 'checkout'
GRAPH = 'graph'
BRANCH = 'branch'
WIT = 'wit'
WIT_FOLDER = '.wit'
IMAGES = 'images'
STAGING = 'staging'
STAGING_PATH = r'\.wit\staging'
LETTERS_FOR_ID_COMMIT = '1234567890abcdef'
IMAGES_PATH = r'\.wit\images'
DATE_FORMAT = '%a %b %d %H:%M:%S %Y %z'
REFERENCES_FILE = r'\.wit\references.txt'
MASTER = 'master'
TXT = '.txt'
HEAD = 'HEAD'
ALL = '--all'
NONE = 'None'
ACTIVATED_PATH = r'\.wit\activated.txt'
INIT_CONTENT = ''
REFERENCES_FILE_CONTENT = 'master='


def init_logger():
    # The basic of the Code is from Logging HOWTO website that create a logger and stream handler
    # to print the log to console
    # https://docs.python.org/3/howto/logging.html
    # By Vinay Sajip
    logger = logging.getLogger('wit_logger')
    logger.setLevel(logging.ERROR)
    stream_logging_handler = logging.StreamHandler()
    stream_logging_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_logging_handler.setFormatter(formatter)
    logger.addHandler(stream_logging_handler)
    return logger


def create_folder(path):
    try:
        os.mkdir(path)
    except FileExistsError as err:
        wit_logger.info(err)
    except OSError as err:
        wit_logger.debug(f'Error during create the dir "{path}" {err}')


def copy_file(src, dest):
    try:
        shutil.copy2(src, dest)
    except FileExistsError as err:
        wit_logger.info(err)
    except OSError as err:
        wit_logger.debug(f'Error during copy file "{src} to {dest}" {err}')


def create_folders(folders_paths):
    for path in folders_paths:
        if not os.path.exists(path):
            create_folder(path)


def generate_paths(current_path):
    wit_path = os.path.join(current_path, WIT_FOLDER)
    images_path = os.path.join(wit_path, IMAGES)
    staging_area = os.path.join(wit_path, STAGING)
    return (wit_path, images_path, staging_area)


def init():
    wit_logger.debug('Get current dir')
    current_path = os.getcwd()
    wit_logger.debug('Start creating folders if dose not exist')
    create_folders(generate_paths(current_path))
    write_content_to_file(current_path + ACTIVATED_PATH, 'master')
    write_content_to_file(current_path + REFERENCES_FILE, REFERENCES_FILE_CONTENT)
    wit_logger.debug('End create folders')


def find_folder_in_path(path, folder_to_find):
    wit_path = path
    found_folder = False

    while found_folder is False:
        dirs = filter(lambda dir: os.path.isdir(os.path.join(wit_path, dir)), os.listdir(wit_path))
        if folder_to_find in dirs:
            return wit_path
        else:
            if wit_path != os.path.dirname(wit_path):
                wit_path = os.path.dirname(wit_path)
            else:
                return False


def copy_filesystem_tree(source, dest):
    if os.path.isdir(source):
        files = [file for file in os.listdir(source) if os.path.isfile(os.path.join(source, file))]
        for file in files:
            copy_file(os.path.join(source, file), dest)

        dirs = [folder for folder in os.listdir(source) if os.path.isdir(os.path.join(source, folder))]

        for folder in dirs:
            new_dir = os.path.join(dest, folder)
            if not os.path.exists(new_dir):
                create_folder(new_dir)
            copy_filesystem_tree(os.path.join(source, folder), new_dir)
    else:
        copy_file(source, dest)


def get_folders_to_copy(absolute_path, wit_path):
    abs_folders_path = list(Path(absolute_path).parts)
    wit_folders_path = list(Path(wit_path).parts)
    folders_to_copy = [folder for folder in abs_folders_path if folder not in wit_folders_path]
    return folders_to_copy


def get_absolute_path(path):
    if os.path.realpath(path) == path:
        return path
    return os.path.join(os.getcwd(), os.path.normpath(path))


def create_destination_path(folders_to_copy, source_path_to_copy, dir_to_create_in_staging):
    for folder in folders_to_copy:
        source_path_to_copy = os.path.join(source_path_to_copy, folder)
        if os.path.isdir(source_path_to_copy):
            dir_to_create_in_staging = os.path.join(dir_to_create_in_staging, folder)
            create_folder(dir_to_create_in_staging)
    return source_path_to_copy, dir_to_create_in_staging


def add(path):
    absolute_path = get_absolute_path(path)
    if os.path.exists(absolute_path):
        wit_path = find_folder_in_path(os.path.dirname(absolute_path), WIT_FOLDER)
        if wit_path:
            folders_to_copy = get_folders_to_copy(absolute_path, wit_path)
            source_path_to_copy = wit_path
            dir_to_create_in_staging = wit_path + STAGING_PATH
            source_path_to_copy, dir_to_create_in_staging = create_destination_path(folders_to_copy,
                                                                                    source_path_to_copy,
                                                                                    dir_to_create_in_staging)
            copy_filesystem_tree(source_path_to_copy, dir_to_create_in_staging)
        else:
            wit_logger.critical('There is no WIT folder at this path')
            return False
        return True
    else:
        wit_logger.error(f'Path {path} dose not exist')


def generate_commit_id():
    return ''.join([random.choice(LETTERS_FOR_ID_COMMIT) for _ in range(40)])


def write_content_to_file(path, content, mode='w'):
    try:
        with open(path, mode) as commit_file:
            commit_file.write(content)
    except FileExistsError as err:
        wit_logger.info(err)
    except OSError as err:
        wit_logger.debug(f'Error during create the dir "{path}" {err}')


def create_commit_file_content(msg, parent=None):
    return (f'parent={parent}\n'
            f'date={datetime.now(timezone.utc).astimezone().strftime(DATE_FORMAT)}\n'
            f'message={msg}\n')


def create_reference_file_content(path, branch=None, branch_commit=None, head=None):
    ref_lines = []
    is_head_found = False

    for line in readlines_file(path):
        new_line = line
        branch_name, commit_id = new_line.split('=')

        if branch_name == HEAD and head is not None:
            is_head_found = True
            new_line = '='.join([new_line.split('=')[0], head])

        if branch is not None:
            if branch == branch_name:
                new_line = '='.join([new_line.split('=')[0], branch_commit])
        ref_lines.append(new_line.strip('\n'))

    if not is_head_found:
        ref_lines.insert(0, f'{HEAD}={branch_commit}')
    return '\n'.join(ref_lines)


def readlines_file(path):
    try:
        with open(path, 'r') as file:
            file_lines = file.readlines()
    except FileNotFoundError as err:
        wit_logger.error(err)
    except PermissionError as err:
        wit_logger.error(err)
    else:
        return file_lines


def get_data_from_references_file_by_index(path, index):
    reference_lines = readlines_file(path)
    try:
        return reference_lines[index].split('=')[1].strip('\n')
    except IndexError as err:
        wit_logger.critical(err)
        wit_logger.error('There is no data in references file')
        return None
    except TypeError as err:
        wit_logger.critical(err)
        wit_logger.error('There is no data in references file')


def get_wit_parent_path():
    current_dir = os.getcwd()
    return find_folder_in_path(os.path.dirname(current_dir), WIT_FOLDER)


def commit(msg):
    wit_parent_path = get_wit_parent_path()
    if wit_parent_path:
        commit_id = generate_commit_id()
        commit_dir_to_create_in_images = wit_parent_path + IMAGES_PATH
        commit_folder = os.path.join(commit_dir_to_create_in_images, commit_id)
        create_folder(commit_folder)
        commit_file = os.path.join(commit_dir_to_create_in_images, commit_id + TXT)
        reference_file_path = wit_parent_path + REFERENCES_FILE
        head = get_data_from_references_file_by_index(reference_file_path, 0)
        parent = head
        commit_file_content = create_commit_file_content(msg, parent)
        write_content_to_file(commit_file, commit_file_content)
        wit_logger.debug('Commit Folder and File was created')

        staging_path = wit_parent_path + STAGING_PATH
        copy_filesystem_tree(staging_path, commit_folder)
        wit_logger.debug('Staging data copied to images folder')
        activated_branch = get_branch_in_activated_file(wit_parent_path)
        branch_commit = get_commit_from_ref_file_by_branch(reference_file_path, activated_branch)
        if branch_commit == head and head is not None:
            reference_file_content = create_reference_file_content(path=reference_file_path, branch=activated_branch,
                                                                   branch_commit=commit_id, head=commit_id)
        else:
            reference_file_content = create_reference_file_content(path=reference_file_path, head=commit_id)
        write_content_to_file(reference_file_path, reference_file_content)
        wit_logger.debug('Content written to references file')
    else:
        wit_logger.critical('There is no WIT folder at this path')


def get_full_path_files(path):
    full_path_files = []
    for paths, _, files in os.walk(path):
        for file in files:
            full_path_files.append(os.path.join(paths, file))
    return full_path_files


def get_originals_path_files(path, string_to_replace, replace_text=""):
    originals = []
    for file in get_full_path_files(path):
        originals.append(replace_content_in_path(file, string_to_replace, replace_text))
    return originals


def replace_content_in_path(path, text_to_replace, text_to_enter=""):
    return path.replace(text_to_replace, text_to_enter)


def get_uncommited_files_in_staging(staging_path, images_path, head, wit_parent_path):
    staging_paths = set(get_originals_path_files(staging_path, STAGING_PATH))
    images_paths = set(get_originals_path_files(images_path, os.path.join(IMAGES_PATH, head)))
    uncommited_files = staging_paths.difference(images_paths)
    commited_files_for_check_content = staging_paths.intersection(images_paths)
    changes_to_be_commited = list(uncommited_files)

    for file in commited_files_for_check_content:
        staging_file = replace_content_in_path(file, wit_parent_path, wit_parent_path + STAGING_PATH)
        image_file = replace_content_in_path(file, wit_parent_path, wit_parent_path + os.path.join(IMAGES_PATH, head))
        if not filecmp.cmp(staging_file, image_file):
            changes_to_be_commited.append(staging_file)

    return changes_to_be_commited


def get_difference_files_in_staging(staging_path):
    staging_files = get_full_path_files(staging_path)
    original_files = get_originals_path_files(staging_path, STAGING_PATH)
    staging_files.sort()
    original_files.sort()
    difference_files = []
    for index in range(len(staging_files)):
        try:
            if not filecmp.cmp(staging_files[index], original_files[index]):
                difference_files.append(original_files[index])
        except FileNotFoundError:
            logging.error(f'File {original_files[index]} was deleted at original folder')
    return difference_files


def get_untracked_files(wit_parent_path, staging_path):
    all_files_under_wit_parent_path = get_full_path_files(wit_parent_path)
    all_files_under_wit_parent_path_without_wit = set(
        filter(lambda path: WIT_FOLDER not in path, all_files_under_wit_parent_path))
    staging_files = set(get_originals_path_files(staging_path, STAGING_PATH))
    untracked_files = all_files_under_wit_parent_path_without_wit.difference(staging_files)
    return untracked_files


def show_status(wit_status):
    for status, values in wit_status.items():
        print(status)
        if not len(values) == 0:
            for value in values:
                print(value)
        print()


def status():
    wit_status = {
        'Head': [],
        'Changes to be committed': [],
        'Changes not staged for commit': [],
        'Untracked files': [],
    }

    wit_parent_path = get_wit_parent_path()
    if wit_parent_path:
        reference_file_path = wit_parent_path + REFERENCES_FILE
        images_path = wit_parent_path + IMAGES_PATH
        head = get_data_from_references_file_by_index(reference_file_path, 0)
        if head is None:
            is_empty = True
            wit_logger.error('There is no commits')
            return wit_status, is_empty
        else:
            is_empty = False
            last_commit_folder = os.path.join(images_path, head)
            staging_path = wit_parent_path + STAGING_PATH
            files_to_be_commited = get_uncommited_files_in_staging(staging_path, last_commit_folder, head,
                                                                   wit_parent_path)
            diff_staged_original_files = get_difference_files_in_staging(staging_path)
            untracked_files = get_untracked_files(wit_parent_path, staging_path)
            wit_status['Head'].append(head)
            wit_status['Changes to be committed'] = files_to_be_commited
            wit_status['Changes not staged for commit'] = diff_staged_original_files
            wit_status['Untracked files'] = untracked_files
            return wit_status, is_empty
    else:
        wit_logger.critical('There is no WIT folder at this path')


def update_head_in_references_file(head, wit_parent_path):
    reference_file_path = wit_parent_path + REFERENCES_FILE
    reference_file_content = create_reference_file_content(path=reference_file_path, head=head)
    write_content_to_file(reference_file_path, reference_file_content)
    wit_logger.debug('New head written to references file')


def removes_tree(path):
    shutil.rmtree(path)


def replace_staging_with_image(wit_parent_path, commit_folder_full_path):
    staging_path = wit_parent_path + STAGING_PATH
    try:
        removes_tree(staging_path)
    except FileNotFoundError as err:
        wit_logger.error(err)
    else:
        create_folder(staging_path)
        copy_filesystem_tree(commit_folder_full_path, staging_path)


def copy_files(dest_files, src_files):
    dest_files.sort()
    src_files.sort()
    for index in range(len(dest_files)):
        copy_file(dest_files[index], src_files[index])


def get_commit_from_ref_file_by_branch(path, branch_name):
    for line in readlines_file(path):
        name, commit_id = line.split('=')
        if name == branch_name:
            return commit_id.strip('\n')
    return None


def checkout(commit_id):
    wit_parent_path = get_wit_parent_path()
    if wit_parent_path:
        curr_status, is_empty = status()
        if is_empty:
            wit_logger.error('There is no commit to checkout to')
        else:
            if curr_status.get('Changes to be committed') == [] and curr_status.get(
                    'Changes not staged for commit') == []:

                reference_file_path = wit_parent_path + REFERENCES_FILE
                active_branch = get_branch_in_activated_file(wit_parent_path)
                if active_branch != commit_id:
                    branch_commit = get_commit_from_ref_file_by_branch(reference_file_path, commit_id)
                    if branch_commit is not None:
                        write_content_to_file(wit_parent_path + ACTIVATED_PATH, commit_id)
                        commit_id = branch_commit
                    else:
                        # clean activate
                        write_content_to_file(wit_parent_path + ACTIVATED_PATH, INIT_CONTENT)

                    commit_folder = os.path.join(IMAGES_PATH, commit_id)
                    commit_folder_full_path = wit_parent_path + commit_folder
                    image_files = get_full_path_files(commit_folder_full_path)
                    original_files = get_originals_path_files(commit_folder_full_path, commit_folder)
                    copy_files(image_files, original_files)
                    update_head_in_references_file(commit_id, wit_parent_path)
                    replace_staging_with_image(wit_parent_path, commit_folder_full_path)
                    wit_logger.info(f'Checkout to {commit_id}')
                else:
                    wit_logger.info('You currently on this branch')
            else:
                wit_logger.error('There is file in staged, save changes (commit) before using checkout')
    else:
        wit_logger.critical('There is no WIT folder at this path')


def get_parents_from_commit_file(commit_file):
    files_lines = readlines_file(commit_file)
    parents = files_lines[0].split('=')[1].strip('\n')
    parents = parents.split(',')
    return parents


def trim_nodes(node):
    return node[:6]


def create_nodes_and_connections(commit_id, head, commit_graph, wit_parent_path, master):
    while commit_id != '':
        commits_id_from_parent = get_next_commit_id(commit_id, wit_parent_path)
        commit_id = trim_nodes(commit_id)
        commit_graph.node(commit_id)

        if commit_id == trim_nodes(master):
            commit_graph.edge(MASTER, commit_id)
        if commit_id == trim_nodes(head):
            commit_graph.edge(HEAD, commit_id)

        if len(commits_id_from_parent) > 1:
            for commit in commits_id_from_parent:
                commit_graph.edges([commit_id + commit])
                commit_graph = create_nodes_and_connections(commit, head, commit_graph, wit_parent_path, master)
        else:
            one_commit = trim_nodes(commits_id_from_parent[0])
            if one_commit != '':
                commit_graph.node(one_commit)
                commit_graph.edge(commit_id, one_commit)
            commit_id = commits_id_from_parent[0]
    return commit_graph


def get_next_commit_id(commit_id, wit_parent_path):
    commit_file = os.path.join(IMAGES_PATH, commit_id + TXT)
    commit_folder_full_path = wit_parent_path + commit_file
    parents = get_parents_from_commit_file(commit_folder_full_path)
    return parents


def get_all_commit_files(images_path):
    return [commit_file for commit_file in os.listdir(images_path) if
            os.path.isfile(os.path.join(images_path, commit_file))]


def init_graph():
    commit_graph = Digraph('commit-diagram', filename='commit_graph.gv')
    commit_graph.attr('node', shape='circle', style='filled', fillcolor='azure')
    commit_graph.attr(rankdir='RL', size='4,5')
    commit_graph.node(MASTER, style='filled', fillcolor='green')
    commit_graph.node(HEAD, style='filled', fillcolor='yellow')
    return commit_graph


def graph():
    wit_parent_path = get_wit_parent_path()
    if wit_parent_path:
        reference_file_path = wit_parent_path + REFERENCES_FILE
        head = get_data_from_references_file_by_index(reference_file_path, 0)
        master = get_data_from_references_file_by_index(reference_file_path, 1)
        commit_graph = init_graph()
        commit_graph = create_nodes_and_connections(head, head, commit_graph, wit_parent_path, master)
        commit_graph.view()
    else:
        wit_logger.critical('There is no WIT folder at this path')


def get_branch_in_activated_file(wit_parent_path):
    file_lines = readlines_file(wit_parent_path + ACTIVATED_PATH)
    return file_lines[0]


def branch(branch_name):
    wit_parent_path = get_wit_parent_path()
    if wit_parent_path:
        reference_file_path = wit_parent_path + REFERENCES_FILE
        head = get_data_from_references_file_by_index(reference_file_path, 0)
        content = f'\n{branch_name}={head}'
        write_content_to_file(reference_file_path, content, 'a')

    else:
        wit_logger.critical('There is no WIT folder at this path')


if __name__ == '__main__':
    wit_logger = init_logger()
    init()
    if len(sys.argv) == 2 and sys.argv[1] == INIT:
        init()
    elif sys.argv[1] == ADD:
        if len(sys.argv) > 2:
            if add(sys.argv[2]):
                wit_logger.info(f'The path {sys.argv[2]} was added')
        else:
            wit_logger.error('file must be enterd to be added')
    elif sys.argv[1] == COMMIT:
        if len(sys.argv) == 3:
            commit(msg=sys.argv[2])
            wit_logger.info('The commit succeeded')
        else:
            wit_logger.info('MSG must be entered')
    elif len(sys.argv) == 2 and sys.argv[1] == STATUS:
        wit_stat = status()
        show_status(wit_stat[0])
    elif sys.argv[1] == CHECKOUT:
        if len(sys.argv) == 3:
            checkout(commit_id=sys.argv[2])
        else:
            wit_logger.error('Checkout must get commit_id or master')
    elif sys.argv[1] == GRAPH:
        if len(sys.argv) > 2:
            graph()
        else:
            graph()
    elif sys.argv[1] == BRANCH:
        if len(sys.argv) > 2:
            branch(sys.argv[2])
        else:
            wit_logger.error('Branch must get commit_id or branch name')
    else:
        try:
            wit_logger.critical(f'{sys.argv[1]} is not wit command')
        except IndexError:
            wit_logger.critical('Enter parameter to use wit')
