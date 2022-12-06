#!/usr/bin/env python3

from pathlib import Path
from typing import Sequence
from typing import Tuple
import os
import sys

IGNORE_FILE_SUFFIX = [
  ".bp",  # Android.bp file is not a target.
  ".md",
  ".mk",  # We are not using make files.
  ".pl",
  ".py",
  ".txt",
  ".yml",
]

# list of specific files to be ignored.
IGNORE_FILE_NAME = [
  # Unused files mostly for build script for Linux.
  "Makefile",
  "autogen.sh",
  "configure",
  "meson.build", # For meson
  "modules.cfg", # For GNU make
  "src/base/ftver.rc", # For Windows DLL.
  "vms_make.com",

  # project config files
  ".clang-format",
  ".gitignore",
  ".mailmap",
  "objs/.gitignore",

  # Android specific files. (i.e. not available in upstream)
  "LICENSE",
  "METADATA",
  "MODULE_LICENSE_BSD_LIKE",
  "NOTICE",
  "OWNERS",
  "TEST_MAPPING",
  "include/freetype/config/ftmodule.h",  # config file. modified for Android.

  # Readme files
  "objs/README",
  "README",
  "README.android",
  "README.git",
  "src/bdf/README",
  "src/gxvalid/README",
  "src/pcf/README",

  # data files
  "src/autofit/afblue.cin",
  "src/autofit/afblue.dat",
  "src/autofit/afblue.hin",

  # MD5 implementation is not necessary in release build.
  "src/base/md5.h",
  "src/base/md5.c",

  # gzip uses system zlib instead of checked in codes.
  "src/gzip/adler32.c",
  "src/gzip/ftzconf.h",
  "src/gzip/infblock.c",
  "src/gzip/infblock.h",
  "src/gzip/infcodes.c",
  "src/gzip/infcodes.h",
  "src/gzip/inflate.c",
  "src/gzip/inftrees.c",
  "src/gzip/inftrees.h",
  "src/gzip/infutil.c",
  "src/gzip/infutil.h",
  "src/gzip/zlib.h",
  "src/gzip/zutil.c",
  "src/gzip/zutil.h",

  # other ignored files.
  "include/freetype/ftchapters.h",  # template
  "src/gzip/inffixed.h", # generated file

]

IGNORE_TOP_LEVEL_DIRS = [
  # Unused directory, build scripts, docs, tools and tests.
  "builds",
  "docs",
  "src/tools",
  "subprojects",
  "tests",

  # Android specific directory.
  "devel-teeui",

  # Following directories are for disabled modules.
  "src/bdf",
  "src/cache",
  "src/gxvalid",
  "src/lzw",
  "src/otvalid",
  "src/pcf",
  "src/pfr",
  "src/type42",
  "src/winfonts",
]

# Helper function of showing error message and immediate exit.
def fatal(msg: str):
  sys.stderr.write(msg)
  sys.stderr.write("\n")
  sys.exit(1)

# Returns true if the given line is a end of copyright notice.
def is_copyright_end(line: str) -> bool:
  if "*/" in line:
    return True
  if "understand and accept it fully." in line:
    return True
  return False

# Extract copyright notice and returns next index.
def extract_copyright_at(lines: Sequence[str], i: int) -> Tuple[str, int]:
  start = i
  while i < len(lines):
    if is_copyright_end(lines[i]):
      break
    i += 1
  end = i + 1

  if start == end:
    fatal("Failed to get copyright info")

  out_lines = []
  for line in lines[start:end]:
    if line.startswith(" * "):
      out_lines.append(line[3:])
    elif line == " *":
      out_lines.append(line[2:])
    elif line == " */":
      pass
    elif line == "*/":
      pass
    else:
      out_lines.append(line)

  while not out_lines[-1].strip():
    out_lines.pop(-1)

  res = "\n".join(out_lines)
  if not res:
    fatal("Failed to get copyright info")

  return (res, i + 1)

# Returns true if the line shows the start of copyright notice.
def is_copyright_line(line: str) -> bool:
  if "Copyright" not in line:
    return False

  # For avoiding unexpected mismatches, exclude quoted Copyright string.
  if "`Copyright'" in line: # For src/psaux/psobjs.c
    return False
  if "\"Copyright\"" in line:  # For src/cff/cfftoken.h
    return False
  return True

# Returns true if the file path is a target of the copyright notice collection.
def is_target_file(fpath: str) -> bool:
  path = Path(fpath)

  if path.suffix.lower() in IGNORE_FILE_SUFFIX:
    return False
  if fpath in IGNORE_FILE_NAME:
    return False

  return True

# Extract the copyright notice and put it into copyrights arg.
def do_file(path: str, copyrights: set):
  raw = Path(path).read_bytes()
  try:
    content = raw.decode("utf-8")
  except UnicodeDecodeError:
    fatal("The file content is not UTF-8")

  lines = content.splitlines()

  if not "Copyright" in content:
    fatal("%s doens't have copyright info" % path)

  i = 0
  while i < len(lines):
    if is_copyright_line(lines[i]):
      (notice, nexti) = extract_copyright_at(lines, i)
      validate(notice, path)

      i = nexti
      copyrights.add(notice)
    else:
      i += 1

# Easy validation for the copyright text.
def validate(text: str, path: str):
  if '/*' in text:
    fatal('/* found in the copyright text in %s. \n%s' % (path, text))
  if '*/' in text:
    fatal('*/ found in the copyright text in %s. \n%s' % (path, text))

def do_check(path):
  if not path.endswith('/'): # make sure the path ends with slash
    path = path + '/'

  copyrights = set()

  ignore_abs_dirs = [os.path.join(path, x) for x in IGNORE_TOP_LEVEL_DIRS]
  for directory, sub_directories,  filenames in os.walk(path):
    # skip .git directory
    if ".git" in sub_directories:
      sub_directories.remove(".git")

    # Skip directory that is in the ignore list.
    for subdir in sub_directories[:]:
      if os.path.join(directory, subdir) in ignore_abs_dirs:
        sub_directories.remove(subdir)

    for fname in filenames:
      fpath = os.path.join(directory, fname)
      rel_path = os.path.join(directory, fname)[len(path):]
      if not is_target_file(rel_path):
        continue
      do_file(fpath, copyrights)

  # print the copyright in sorted order for stable output.
  for notice in sorted(copyrights):
    print(notice)
    print()
    print("-" * 67)
    print()

def main():
  do_check(sys.argv[1])

if __name__ == "__main__":
  main()

