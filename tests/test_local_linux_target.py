import os
import tempfile
import pytest

from devlib import LocalLinuxTarget


@pytest.fixture(scope="class")
def target():
    target = LocalLinuxTarget(connection_settings={'unrooted': True})
    yield target
    target.disconnect()


class TestLocalLinuxMethods:
    '''
    Verify basic functionality of LocalTarget and LocalConnection
    '''

    def test_connection(self, target):
        target.check_connection()

    def test_echo(self, target):
        expected = 'A TEST STRING'
        assert target.execute('echo {}'.format(expected)).strip() == expected

    def test_busybox_echo(self, target):
        assert target.file_exists(target.busybox)
        expected = 'A TEST STRING'
        assert target.execute('{} echo {}'.format(target.busybox, expected)).strip() == expected

    def test_background_command(self, target):
        expected = 'A TEST STRING'
        bg_cmd = target.background('echo {}'.format(expected))
        assert bg_cmd
        bg_cmd.wait()
        assert bg_cmd.stdout.read().strip().decode('utf-8') == expected

    def test_get_work_directory(self, target):
        assert target.get_workpath('test')

    def test_push(self, target):
        with tempfile.NamedTemporaryFile() as src_file:
            dst = target.get_workpath('test')
            target.push(src_file.name, dst)
        assert target.file_exists(dst)
        target.remove(dst)

    def test_pull(self, target):
        src = target.get_workpath('test')
        target.execute('touch {}'.format(src))
        dst = tempfile.NamedTemporaryFile().name
        target.pull(src, dst)
        assert os.path.exists(dst)
        os.remove(dst)
        target.remove(dst)

    def test_installation(self, target):
        bin_name = 'test_binary'
        with tempfile.NamedTemporaryFile() as src_file:
            path = target.install(src_file.name, with_name=bin_name)
            assert path
            assert target.is_installed(bin_name)
            target.uninstall(bin_name)

    def test_shutils_setup(self, target):
        assert target.shutils

    def test_directories_exists(self, target):
        assert target.directory_exists(target.working_directory)
        assert target.directory_exists(target.executables_directory)


class TestLocalTargetAttributes:

    '''
    Exercise target attributes, we don't know the machine the
    tests will be running on, only root status, so just check the
    call executes correctly.
    '''

    def test_core_name(self, target):
        assert target.core_names

    def test_clusters(self, target):
        assert target.core_names

    def test_is_connected(self, target):
        assert target.is_connected

    def test_not_connected_as_root(self, target):
        assert not target.connected_as_root

    def test_is_unrooted(self, target):
        assert not target.is_rooted

    def test_needs_su(self, target):
        assert not target.needs_su

    def test_kernel_version(self, target):
        assert target.kernel_version

    def test_hostid(self, target):
        assert target.hostid is not None

    def test_hostname(self, target):
        assert target.hostname is not None

    def test_os_version(self, target):
        assert target.os_version is not None

    def test_model(self, target):
        target.model  # Likely to be None

    def test_abi(self, target):
        assert target.abi is not None

    def test_cpuinfo(self, target):
        assert target.cpuinfo is not None

    def test_number_of_cpus(self, target):
        assert target.number_of_cpus is not None

    def test_number_of_nodes(self, target):
        assert target.number_of_nodes is not None

    def test_list_nodes_cpus(self, target):
        assert target.list_nodes_cpus is not None

    def test_config(self, target):
        assert target.config is not None

    def test_user(self, target):
        assert target.user is not None

    def test_page_size_kb(self, target):
        assert target.user is not None

    def test_page_size_kb(self, target):
        assert target.user is not None
