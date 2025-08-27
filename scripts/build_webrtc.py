import argparse
import os
import platform
import shutil
import stat
import subprocess
import sys

script_dir: str = os.path.dirname(os.path.abspath(__file__))
working_dir: str = os.path.abspath(os.path.join(script_dir, '..', 'webrtc'))
patches_dir: str = os.path.join(working_dir, 'patches')
webrtc_dir: str = os.path.join(working_dir, 'webrtc')
webrtc_src_dir: str = os.path.join(webrtc_dir, 'src')
external_dir: str = os.path.abspath(os.path.join(script_dir, '..', 'external'))
dist_dir: str = os.path.join(external_dir, 'webrtc')
dist_lib_dir: str = os.path.join(dist_dir, 'lib')
dist_inc_dir: str = os.path.join(dist_dir, 'include')

system_platform: str = platform.system().lower()
system_architecture: str = platform.machine().lower()

args: argparse.Namespace = None
env: dict[str, str] = os.environ.copy()

def main():
	parse_args()

	print(f'Platform: {system_platform}')
	print(f'Architecture: {system_architecture}')

	install_prerequisites()

	if args.command == 'run' or args.command == 'fetch':
		fetch_source()
	if args.command == 'run' or args.command == 'build':
		configure_build()
		build()
	if args.command == 'run' or args.command == 'dist':
		distribute()

def parse_args():
	arg_parser = argparse.ArgumentParser(description='Build WebRTC.', formatter_class=argparse.RawTextHelpFormatter)
	cmd_parser = arg_parser.add_subparsers(title='command', dest='command', help='')

	def add_debug_argument(parser: argparse.ArgumentParser):
		parser.add_argument('--debug', type=str_to_bool, default=False, help='Compile a debug build.')

	def add_branch_argument(parser: argparse.ArgumentParser):
		parser.add_argument('--branch', type=str, help='Optional branch to check out (e.g. branch-heads/7204).')

	run_parser = cmd_parser.add_parser('run', help='Run all build steps.')
	add_debug_argument(run_parser)
	add_branch_argument(run_parser)

	fetch_parser = cmd_parser.add_parser('fetch', help='Fetch source.')
	add_branch_argument(fetch_parser)

	build_parser = cmd_parser.add_parser('build', help='Build.')
	add_debug_argument(build_parser)
	add_branch_argument(build_parser)

	dist_parser = cmd_parser.add_parser('dist', help='Distribute build output.')

	global args
	args = arg_parser.parse_args()

def install_prerequisites():
	print('📦 Install prerequisites')

	if system_platform == 'windows':
		check_windows_environment()
		enable_git_longpaths()

	get_depot_tools()

def fetch_source():
	print('📁 Fetch source')

	if not os.path.exists(webrtc_dir):
		os.makedirs(webrtc_dir)
		print(f'✅ Created source directory: {webrtc_dir}')

		try:
			print('⏳ Fetching source...')
			subprocess.run(
				f'fetch --nohooks webrtc',
				cwd=webrtc_dir,
				env=env,
				check=True,
				shell=True,
				stdout=sys.stdout,
				stderr=sys.stderr
			)
			print('✅ Success fetching source')
		except FileNotFoundError:
			print('❌ Error fetching source: Command fetch not found, depot_tools may not be in PATH')
			sys.exit(1)
		except subprocess.CalledProcessError as e:
			print(f'❌ Error fetching source: {e}')
			sys.exit(1)

		if args.branch:
			checkout_branch(args.branch)

		sync_deps()

		apply_patches()
	else:
		print(f'✅ Found source directory: {webrtc_dir}')

def configure_build():
	print('⚙️ Configure build')

	common_gn_args = [
		'is_component_build=false',
		'rtc_build_examples=false',
		'rtc_build_tools=false',
		'rtc_include_tests=false',
		'treat_warnings_as_errors=false',
		'use_rtti=true',
	]

	linux_gn_args = [
		'is_clang=true',
		'use_custom_libcxx=false',
	]

	mac_gn_args = [
		'is_clang=true',
		'use_custom_libcxx=false',
	]

	windows_gn_args = [
		'is_clang=true',
		'use_custom_libcxx=false',
	]

	target_os = get_target_os()
	target_cpu = get_target_cpu()

	gn_args = [
		f'target_os=\\"{target_os}\\"',
		f'target_cpu=\\"{target_cpu}\\"',
		f'is_debug={"true" if args.debug else "false"}',
		*common_gn_args,
	]

	if system_platform == 'linux':
		gn_args += linux_gn_args
	if system_platform == 'mac':
		gn_args += mac_gn_args
	if system_platform == 'windows':
		gn_args += windows_gn_args

	build_args = " ".join(gn_args)
	print('\n'.join(f'{arg}' for arg in gn_args))

	try:
		print('⏳ Configuring build...')
		subprocess.run(
			f'gn gen out/Default --args="{build_args}"',
			cwd=webrtc_src_dir,
			env=env,
			check=True,
			shell=True,
			stdout=sys.stdout,
			stderr=sys.stderr
		)
		print('✅ Success configuring build')
	except subprocess.CalledProcessError as e:
		print(f'❌ Error configuring build: {e}')
		sys.exit(1)

def build():
	print('🔨 Build')

	try:
		print('⏳ Building...')
		subprocess.run(
			f'ninja -C out/Default',
			cwd=webrtc_src_dir,
			env=env,
			check=True,
			shell=True,
			stdout=sys.stdout,
			stderr=sys.stderr
		)
		print('✅ Success building')
	except subprocess.CalledProcessError as e:
		print(f'❌ Error building: {e}')
		sys.exit(1)

def distribute():
	print('🚀 Distribute')

	# Clean directories.
	def remove_readonly(func, path, _):
		os.chmod(path, stat.S_IWRITE)
		func(path)

	for path in [dist_lib_dir, dist_inc_dir]:
		if os.path.exists(path):
			print(f'⏳ Cleaning directory: {path}')
			shutil.rmtree(path, onerror=remove_readonly)
			print('✅ Success cleaning directory')
		os.makedirs(path, exist_ok=True)

	# Copy library.
	lib_name = 'webrtc.lib' if system_platform == 'windows' else 'libwebrtc.a'
	current_lib_dir = os.path.join(webrtc_src_dir, 'out', 'Default', 'obj', lib_name)
	new_lib_dir = os.path.join(dist_lib_dir, lib_name)
	print(f'⏳ Copying library from {current_lib_dir} to {new_lib_dir}...')

	if not os.path.isfile(current_lib_dir):
		print(f'❌ Error copying library: File not found')
		sys.exit(1)
	else:
		shutil.copy2(current_lib_dir, new_lib_dir)
		print('✅ Success copying library')

	# Copy headers.
	print(f'⏳ Copying headers from {webrtc_src_dir} to {dist_inc_dir}...')
	copy_headers(webrtc_src_dir, dist_inc_dir, ['out'])

def str_to_bool(value: str) -> bool:
	if isinstance(value, bool):
		return value
	if value.lower() in ('true', 'yes', 't', 'y', '1'):
		return True
	elif value.lower() in ('false', 'no', 'f', 'n', '0'):
		return False
	else:
		return False

def add_to_path(dir: str):
	current_path = env.get('PATH', '')
	if dir not in current_path:
		env['PATH'] = dir + os.pathsep + current_path
		print(f'✅ Added to PATH: {dir}')
	else:
		print(f'✅ Already in PATH: {dir}')

def get_target_os() -> str:
	if system_platform == 'linux':
		return 'linux'
	elif system_platform == 'darwin':
		return 'mac'
	elif system_platform == 'windows':
		return 'win'
	else:
		print(f'❌ Unsupported platform: {system_platform}')
		sys.exit(1)

def get_target_cpu() -> str:
	if system_architecture in ['x86', 'i386', 'i686']:
		return 'x86'
	elif system_architecture in ['x86_64', 'amd64']:
		return 'x64'
	elif system_architecture in ['arm64', 'aarch64']:
		return 'arm64'
	else:
		print(f'❌ Unsupported architecture: {system_architecture}')
		sys.exit(1)

def get_depot_tools():
	print('⏳ Getting depot_tools...')

	depot_tools_repo = 'https://chromium.googlesource.com/chromium/tools/depot_tools.git'
	depot_tools_dir = os.path.join(working_dir, 'depot_tools')

	if os.path.isdir(depot_tools_dir):
		print(f'✅ Using depot_tools at: {depot_tools_dir}')
	else:
		print(f'⏳ Cloning depot_tools into: {depot_tools_dir}')
		try:
			subprocess.run(
				f'git clone {depot_tools_repo} {depot_tools_dir}',
				check=True,
				stdout=sys.stdout,
				stderr=sys.stderr
			)
			print(f'✅ Success cloning depot_tools')
		except subprocess.CalledProcessError as e:
			print(f'❌ Error cloning depot_tools: {e}')
			sys.exit(1)

	add_to_path(depot_tools_dir)

	if system_platform == 'windows':
		print('✅ Using local Visual Studio toolchain')
		env['DEPOT_TOOLS_WIN_TOOLCHAIN'] = '0'

def check_windows_environment(min_version=(17, 0, 0)):
	vs_architecture = os.environ.get('VSCMD_ARG_TGT_ARCH')
	vs_version = os.environ.get('VSCMD_VER')
	vs_version_semver = tuple(int(part) for part in vs_version.split('.'))
	vc_tools_dir = os.environ.get('VCINSTALLDIR')

	print(f'Visual Studio target architecture: {vs_architecture}')
	print(f'Visual Studio version: {vs_version}')
	print(f'Visual C++: {vc_tools_dir}')

	if vs_architecture == 'x64' and vs_version_semver > min_version and vc_tools_dir:
		print('✅ Running from valid environment')
	else:
		print('❌ Error: Invalid environment, this script must be run from "x64 Native Tools Command Prompt for VS"')
		sys.exit(1)

def enable_git_longpaths():
	try:
		print('⏳ Enabling Git long paths...')
		subprocess.run(
			f'git config --global core.longpaths true',
			env=env,
			check=True,
			shell=True,
			stdout=sys.stdout,
			stderr=sys.stderr
		)
		print('✅ Success enabling Git long paths')
	except subprocess.CalledProcessError as e:
		print(f'❌ Error enabling Git long paths: {e}')
		sys.exit(1)

def checkout_branch(branch: str):
	try:
		print(f'⏳ Checking out branch: {branch}')
		subprocess.run(
			f'git checkout {branch}',
			cwd=webrtc_src_dir,
			env=env,
			check=True,
			shell=True,
			stdout=sys.stdout,
			stderr=sys.stderr
		)
		print(f'✅ Success checking out branch')
	except subprocess.CalledProcessError as e:
		print(f'❌ Error checking out branch: {e}')
		sys.exit(1)

def sync_deps():
	try:
		print(f'⏳ Syncing dependencies...')
		subprocess.run(
			f'gclient sync -D --force --reset --with_branch_heads --with_tags',
			cwd=webrtc_src_dir,
			env=env,
			check=True,
			shell=True,
			stdout=sys.stdout,
			stderr=sys.stderr
		)
		print('✅ Success syncing dependencies')
	except subprocess.CalledProcessError as e:
		print(f'❌ Error syncing dependencies: {e}')
		sys.exit(1)

def apply_patches():
	common_patches = [
	]

	linux_patches = [
	]

	mac_patches = [
	]

	windows_patches = [
	]

	patches = [
		*common_patches,
	]

	if system_platform == 'linux':
		patches += linux_patches
	if system_platform == 'mac':
		patches += mac_patches
	if system_platform == 'windows':
		patches += windows_patches

	for patch in patches:
		patch_path = os.path.join(patches_dir, patch)
		if not os.path.isfile(patch_path):
			print(f'⚠️ Patch not found: {patch_path}')
			continue

		try:
			print(f'⏳ Applying patch: {patch}')
			subprocess.run(
				f'git apply "{patch_path}" -v --ignore-space-change --ignore-whitespace --whitespace=nowarn',
				cwd=webrtc_src_dir,
				env=env,
				check=True,
				shell=True,
				stdout=sys.stdout,
				stderr=sys.stderr
			)
			print('✅ Success aplying patch')
		except subprocess.CalledProcessError as e:
			print(f'❌ Error aplying patch: {e}')
			sys.exit(1)

def copy_headers(src_dir, dst_dir, ignore_dirs=[]):
	count = 0
	for root, _, files in os.walk(src_dir):
		rel_path = os.path.relpath(root, src_dir)
		if any(ignored in rel_path.split(os.sep) for ignored in ignore_dirs):
			continue

		for file in files:
			if file.endswith(('.h', '.hh', '.hpp', '.hxx', '.inc')):
				src_file = os.path.join(root, file)

				# Determine relative path from src_dir and replicate it in dst_dir.
				rel_path = os.path.relpath(root, src_dir)
				dest_dir = os.path.join(dst_dir, rel_path)

				os.makedirs(dest_dir, exist_ok=True)

				dest_file = os.path.join(dest_dir, file)
				shutil.copy2(src_file, dest_file)
				count += 1
	print(f'{"✅" if count > 0 else "❌"} Copied {count} files')

if __name__ == '__main__':
	main()
