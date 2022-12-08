#!/usr/bin/env python3

from enum import Enum
from pathlib import Path
from typing import Sequence
from typing import Tuple
import argparse
import os
import re
import sys

# list of specific files to be ignored.
IGNORE_FILE_NAME = [
  # Exclude myself
  "generate_notice.py",

  # License files
  "LICENSE",
  "LICENSE.TXT",
  "LICENSE_APACHE2.TXT",
  "LICENSE_BSD_3_CLAUSE.TXT",
  "LICENSE_FSFAP.TXT",
  "LICENSE_MIT.TXT",
  "MODULE_LICENSE_BSD_LIKE",
  "NOTICE",
  "builds/unix/LICENSE_GPLv2_WITH_AUTOCONF_EXCEPTION.TXT",
  "builds/unix/LICENSE_GPLv3_WITH_AUTOCONF_EXCEPTION.TXT",
  "docs/FTL.TXT",
  "docs/GPLv2.TXT",
  "src/gzip/LICENSE_ZLIB.TXT",
]

NO_COPYRIGHT_FILES = [
  ".clang-format",
  ".gitignore",
  ".gitlab-ci.yml",
  ".mailmap",
  "Android.bp",
  "METADATA",
  "OWNERS",
  "README.android",
  "TEST_MAPPING",
  "builds/atari/ATARI.H",
  "builds/atari/FNames.SIC",
  "builds/atari/FREETYPE.PRJ",
  "builds/atari/README.TXT",
  "builds/atari/deflinejoiner.awk",
  "builds/atari/gen-purec-patch.sh",
  "builds/mac/FreeType.m68k_cfm.make.txt",
  "builds/mac/FreeType.m68k_far.make.txt",
  "builds/mac/FreeType.ppc_carbon.make.txt",
  "builds/mac/FreeType.ppc_classic.make.txt",
  "builds/mac/README",
  "builds/mac/ascii2mpw.py",
  "builds/mac/freetype-Info.plist",
  "builds/mac/ftlib.prj.xml",
  "builds/unix/.gitignore",
  "builds/unix/freetype2.in",
  "builds/vms/LIBS.OPT_IA64",
  "builds/vms/_LINK.OPT_IA64",
  "builds/vms/vmslib.dat",
  "builds/wince/vc2005-ce/freetype.sln",
  "builds/wince/vc2005-ce/freetype.vcproj",
  "builds/wince/vc2005-ce/index.html",
  "builds/wince/vc2008-ce/freetype.sln",
  "builds/wince/vc2008-ce/freetype.vcproj",
  "builds/wince/vc2008-ce/index.html",
  "builds/windows/.gitignore",
  "builds/windows/vc2010/freetype.sln",
  "builds/windows/vc2010/freetype.user.props",
  "builds/windows/vc2010/freetype.vcxproj",
  "builds/windows/vc2010/freetype.vcxproj.filters",
  "builds/windows/vc2010/index.html",
  "builds/windows/visualc/freetype.dsp",
  "builds/windows/visualc/freetype.dsw",
  "builds/windows/visualc/freetype.sln",
  "builds/windows/visualc/freetype.vcproj",
  "builds/windows/visualc/index.html",
  "builds/windows/visualce/freetype.dsp",
  "builds/windows/visualce/freetype.dsw",
  "builds/windows/visualce/freetype.vcproj",
  "builds/windows/visualce/index.html",
  "devel-teeui/OWNERS",
  "devel-teeui/README.md",
  "devel-teeui/ftmodule.h",
  "devel-teeui/rules.json",
  "devel-teeui/rules.mk",
  "docs/.gitignore",
  "docs/CMAKE",
  "docs/INSTALL.MAC",
  "docs/MAKEPP",
  "docs/PROBLEMS",
  "docs/README",
  "docs/freetype-config.1",
  "docs/markdown/images/favico.ico",
  "docs/markdown/javascripts/extra.js",
  "docs/markdown/stylesheets/extra.css",
  "include/freetype/config/ftmodule.h",
  "include/freetype/ftchapters.h",
  "libft2.map.txt",
  "objs/.gitignore",
  "objs/README",
  "src/gzip/inffixed.h",
  "src/tools/apinames.c",
  "src/tools/chktrcmp.py",
  "src/tools/cordic.py",
  "src/tools/ftrandom/Makefile",
  "src/tools/ftrandom/README",
  "src/tools/make_distribution_archives.py",
  "src/tools/no-copyright",
  "src/tools/test_afm.c",
  "src/tools/test_bbox.c",
  "src/tools/test_trig.c",
  "src/tools/update-copyright",
  "subprojects/libpng.wrap",
  "subprojects/zlib.wrap",
  "tests/README.md",
  "tests/issue-1063/main.c",
  "tests/meson.build",
  "tests/scripts/download-test-fonts.py",
]

class CommentType(Enum):
  C_STYLE_BLOCK = 1  # /* ... */
  C_STYLE_BLOCK_AS_LINE = 2  # /* ... */ but uses multiple lines of block comments.
  C_STYLE_LINE = 3 # // ...
  SCRIPT_STYLE_HASH = 4 #  # ...
  SCRIPT_STYLE_DOLLER = 5 # $! ...
  DOC_STYLE = 6 # no comment escape
  UNKNOWN = 10000


# Helper function of showing error message and immediate exit.
def fatal(msg: str):
  sys.stderr.write(msg)
  sys.stderr.write("\n")
  sys.exit(1)


def warn(msg: str):
  sys.stderr.write(msg)
  sys.stderr.write("\n")


def cleanup_and_join(out_lines: Sequence[str]):
  while not out_lines[-1].strip():
    out_lines.pop(-1)

  # If all lines starts from empty space, strip it out.
  while all([len(x) == 0 or x[0] == ' ' for x in out_lines]):
    out_lines = [x[1:] for x in out_lines]

  if not out_lines:
    fatal("Failed to get copyright info")
  return "\n".join(out_lines)


def get_comment_type(copyright_line: str, path: str) -> CommentType:
  # vms_make.com contains multiple copyright header as a string constants.
  if path.endswith("/vms_make.com"):
    return CommentType.SCRIPT_STYLE_DOLLER

  if "docs/" in path or "README" in path:
    return CommentType.DOC_STYLE

  if copyright_line.startswith("#"):
    return CommentType.SCRIPT_STYLE_HASH
  if copyright_line.startswith("//"):
    return CommentType.C_STYLE_LINE
  if copyright_line.startswith("$!"):
    return CommentType.SCRIPT_STYLE_DOLLER

  if "/*" in copyright_line and "*/" in copyright_line:
    # ftrandom.c uses single line block comment for the first Copyright line,
    # and following license notice is wrapped with single block comment.
    # This file can be handled by C_STYLE_BLOCK parser.
    if path.endswith("src/tools/ftrandom/ftrandom.c"):
      return CommentType.C_STYLE_BLOCK
    else:
      return CommentType.C_STYLE_BLOCK_AS_LINE
  else:
    return CommentType.C_STYLE_BLOCK


# Extract copyright notice and returns next index.
def extract_copyright_at(lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:
  commentType = get_comment_type(lines[i], path)

  if commentType == CommentType.C_STYLE_BLOCK:
    return extract_from_c_style_block_at(lines, i, path)
  if commentType == CommentType.C_STYLE_BLOCK_AS_LINE:
    return extract_from_c_style_block_as_line_at(lines, i, path)
  elif commentType == CommentType.C_STYLE_LINE:
    return extract_from_c_style_lines_at(lines, i, path)
  elif commentType == CommentType.SCRIPT_STYLE_HASH:
    return extract_from_script_hash_at(lines, i, path)
  elif commentType == CommentType.SCRIPT_STYLE_DOLLER:
    return extract_from_script_doller_at(lines, i, path)
  elif commentType == CommentType.DOC_STYLE:
    return extract_from_doc_style_at(lines, i, path)
  else:
    fatal("Uknown comment style: %s" % lines[i])


def extract_from_doc_style_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:
  if not lines[i].startswith("Copyright"):
    return (None, i + 1)

  def is_copyright_end(lines: str, start: int, i: int) -> bool:
    # treat double spacing as end of license header
    if i - start > 4 and lines[i] == "" and lines[i + 1] == "":
      return True
    return False

  start = i
  while i < len(lines):
    if is_copyright_end(lines, start, i):
      break
    i += 1
  end = i

  if start == end:
    fatal("Failed to get copyright info")
  out_lines = lines[start:end]

  return (cleanup_and_join(out_lines), i + 1)


def extract_from_c_style_lines_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:
  def is_copyright_end(line):
    if line.startswith("//"):
      return False
    else:
      return True
  start = i
  while i < len(lines):
    if is_copyright_end(lines[i]):
      break
    i += 1
  end = i

  if start == end:
    fatal("Failed to get copyright info")

  out_lines = []
  for line in lines[start:end]:
    if line.startswith("// "):
      out_lines.append(line[3:])
    elif line == "//":
      out_lines.append(line[2:])
    else:
      out_lines.append(line)

  return (cleanup_and_join(out_lines), i + 1)


def extract_from_script_hash_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:
  if lines[i].strip()[0] != "#":
    return (None, i + 1)
  def is_copyright_end(lines: str, i: int) -> bool:
    if "#" not in lines[i]:
      return True
    # treat double spacing as end of license header
    if lines[i] == "#" and lines[i+1] == "#":
      return True
    return False

  start = i
  while i < len(lines):
    if is_copyright_end(lines, i):
      break
    i += 1
  end = i

  if start == end:
    fatal("Failed to get copyright info")

  out_lines = []
  for line in lines[start:end]:
    if line.startswith("# "):
      out_lines.append(line[2:])
    elif line == "#":
      out_lines.append(line[1:])
    else:
      out_lines.append(line)

  return (cleanup_and_join(out_lines), i + 1)


def extract_from_script_doller_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:
  if not lines[i].strip().startswith("$!"):
    return (None, i + 1)
  def is_copyright_end(lines: str, i: int) -> bool:
    if "$!" not in lines[i]:
      return True
    # treat double spacing as end of license header
    if lines[i] == "$!" and lines[i+1] == "$!":
      return True
    return False

  start = i
  while i < len(lines):
    if is_copyright_end(lines, i):
      break
    i += 1
  end = i + 1

  if start == end:
    fatal("Failed to get copyright info")

  out_lines = []
  for line in lines[start:end]:
    if line.startswith("$! "):
      out_lines.append(line[3:])
    elif line == "$!":
      out_lines.append(line[2:])
    else:
      out_lines.append(line)

  return (cleanup_and_join(out_lines), i + 1)


def extract_from_c_style_block_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:

  def is_copyright_end(lines: str, i: int) -> bool:
    if "*/" in lines[i]:
      return True
    if "understand and accept it fully." in lines[i]:
      return True
    if lines[i] == " *" and lines[i + 1] == " *":
      return True
    if lines[i] == "" and lines[i + 1] == "":
      return True
    return False

  start = i
  i += 1 # include at least one line
  while i < len(lines):
    if is_copyright_end(lines, i):
      break
    i += 1
  end = i + 1

  out_lines = []
  for line in lines[start:end]:
    clean_line = line

    # Strip begining "/*" chars
    if clean_line.startswith("/* "):
      clean_line = clean_line[3:]
    if clean_line == "/*":
      clean_line = clean_line[2:]

    # Strip ending "*/" chars
    if clean_line.endswith(" */"):
      clean_line = clean_line[:-3]
    if clean_line.endswith("*/"):
      clean_line = clean_line[:-2]

    # Strip starting " *" chars
    if clean_line.startswith(" * "):
      clean_line = clean_line[3:]
    if clean_line == " *":
      clean_line = line[2:]

    # Strip trailing spaces
    clean_line = clean_line.rstrip()

    out_lines.append(clean_line)

  return (cleanup_and_join(out_lines), i + 1)


def extract_from_c_style_block_as_line_at(
    lines: Sequence[str], i: int, path: str) -> Tuple[str, int]:

  def is_copyright_end(line: str) -> bool:
    if "*/" in line:
      return False
    if re.match(r'/\*+/', line.strip()):
      return False
    return True

  start = i
  i += 1 # include at least one line
  while i < len(lines):
    if is_copyright_end(lines[i]):
      break
    i += 1
  end = i + 1

  out_lines = []
  for line in lines[start:end]:
    clean_line = line

    if re.match(r'/\*+/', line.strip()):
      continue

    # Strip begining "/*" chars
    if clean_line.startswith("/* "):
      clean_line = clean_line[3:]
    if clean_line == "/*":
      clean_line = clean_line[2:]

    # Strip ending "*/" chars
    if clean_line.endswith(" */"):
      clean_line = clean_line[:-3]
    if clean_line.endswith("*/"):
      clean_line = clean_line[:-2]

    # Strip starting " *" chars
    if clean_line.startswith(" * "):
      clean_line = clean_line[3:]
    if clean_line == " *":
      clean_line = line[2:]

    # Strip trailing spaces
    clean_line = clean_line.rstrip()

    out_lines.append(clean_line)

  return (cleanup_and_join(out_lines), i + 1)

# Returns true if the line shows the start of copyright notice.
def is_copyright_line(line: str, path: str) -> bool:
  if "Copyright" not in line:
    return False

  # For avoiding unexpected mismatches, exclude quoted Copyright string.
  if "`Copyright'" in line: # For src/psaux/psobjs.c
    return False
  if "\"Copyright\"" in line:  # For src/cff/cfftoken.h
    return False

  if (path.endswith("src/tools/update-copyright-year") or
      path.endswith("src/tools/glnames.py")):
    # The comment contains string of Copyright. Use only immediate Copyright
    # string followed by "# ".
    return line.startswith("# Copyright ")

  if path.endswith("src/gzip/inftrees.c"):
    # The unused string constant contains word of Copyright. Use only immediate
    # Copyright string followed by " * ".
    return line.startswith(" * Copyright ")

  if path.endswith("src/base/ftver.rc"):
    # Copyright string matches with LegalCopyright key in the RC file.
    return not "LegalCopyright" in line

  return True


# Extract the copyright notice and put it into copyrights arg.
def do_file(path: str, copyrights: set, no_copyright_files: set):
  raw = Path(path).read_bytes()
  try:
    content = raw.decode("utf-8")
  except UnicodeDecodeError:
    content = raw.decode("iso-8859-1")

  lines = content.splitlines()

  if not "Copyright" in content:
    if path in no_copyright_files:
      no_copyright_files.remove(path)
    else:
      fatal("%s does not contain Copyright line" % path)
    return

  i = 0
  license_found = False
  while i < len(lines):
    if is_copyright_line(lines[i], path):
      (notice, nexti) = extract_copyright_at(lines, i, path)
      if notice:
        if not notice in copyrights:
          copyrights[notice] = []
        copyrights[notice].append(path)
        license_found = True

      i = nexti
    else:
      i += 1

  if not license_found:
    fatal("License header could not found: %s" % path)

def do_check(path, format):
  if not path.endswith('/'): # make sure the path ends with slash
    path = path + '/'

  file_to_ignore = set([os.path.join(path, x) for x in IGNORE_FILE_NAME])
  no_copyright_files = set([os.path.join(path, x) for x in NO_COPYRIGHT_FILES])
  copyrights = {}

  for directory, sub_directories,  filenames in os.walk(path):
    # skip .git directory
    if ".git" in sub_directories:
      sub_directories.remove(".git")

    for fname in filenames:
      fpath = os.path.join(directory, fname)
      if fpath in file_to_ignore:
        file_to_ignore.remove(fpath)
        continue
      do_file(fpath, copyrights, no_copyright_files)

  if len(file_to_ignore) != 0:
    fatal("Following files are listed in IGNORE_FILE_NAME but doesn't exists,.\n"
          + "\n".join(file_to_ignore))

  if len(no_copyright_files) != 0:
    fatal("Following files are listed in NO_COPYRIGHT_FILES but doesn't exists.\n"
          + "\n".join(no_copyright_files))

  if format == Format.notice:
    print_notice(copyrights, False)
  elif format == Format.notice_with_filename:
    print_notice(copyrights, True)
  elif format == Format.html:
    print_html(copyrights)

def print_html(copyrights):
  print('<html>')
  print("""
  <head>
    <style>
      table {
        font-family: monospace
      }

      table tr td {
        padding: 10px 10px 10px 10px
      }
    </style>
  </head>
  """)
  print('<body>')
  print('<table border="1" style="border-collapse:collapse">')
  for notice in sorted(copyrights.keys()):
    files = sorted(copyrights[notice])

    print('<tr>')
    print('<td>')
    print('<ul>')
    for file in files:
      print('<li>%s</li>' % file)
    print('</ul>')
    print('</td>')
    print('<td>')
    print('<p>%s</p>' % notice.replace('\n', '<br>'))
    print('</td>')

    print('</tr>')


  print('</table>')
  print('</body></html>')

def print_notice(copyrights, print_file):
  # print the copyright in sorted order for stable output.
  for notice in sorted(copyrights.keys()):
    if print_file:
      files = sorted(copyrights[notice])
      print("\n".join(files))
      print()
    print(notice)
    print()
    print("-" * 67)
    print()

class Format(Enum):
  notice = 'notice'
  notice_with_filename = 'notice_with_filename'
  html = 'html'

  def __str__(self):
    return self.value

def main():
  parser = argparse.ArgumentParser(description="Collect notice headers.")
  parser.add_argument("--format", dest="format", type=Format, choices=list(Format),
                      default=Format.notice, help="print filename before the license notice")
  parser.add_argument("--target", dest="target", action='store',
                      required=True, help="target directory to collect notice headers")
  res = parser.parse_args()
  do_check(res.target, res.format)

if __name__ == "__main__":
  main()

