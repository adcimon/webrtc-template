import os
import shutil
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.abspath(os.path.join(script_dir, '..'))
build_dir = os.path.join(project_dir, 'build')

def main():
	if os.path.isdir(build_dir):
		try:
			print('🧹 Cleaning...')
			shutil.rmtree(build_dir)
			print('✅ Success cleaning')
		except Exception as e:
			print(f'❌ Error cleaning: {e}')
			sys.exit(1)
	else:
		print('ℹ️ Nothing to clean')

if __name__ == '__main__':
	main()
