# CONFIG
# watch works with ruby 1.9.2

MIRROR_DIR = "../js"

# regex to find the type of import statement used to refer to other files
# here it is //=require "dir/file"
# this refers to dir/file.js
IMPORTRE = /^\/\/=require\s?"[\w_\/]+"\n/
IMPORTREFILE = /^\/\/=require\s?"([\w_\/]+)"\n/


# END OF CONFIG

# TODO
# 
# = A =
# - add prepend files, e.g. jQuery.min.js
# - Wrap watch in try {} catch so doesn't crash when remove files
# 
# = B =
# - make more robust against infinite non-DAG loop
# - make more robust against things like import statements being found in 
#

require 'rubygems'
require 'FSSM'
require 'optparse'

DO_MIN = false; DO_WATCH = false; DO_POLL = false;

optparse = OptionParser.new do|opts|
  opts.banner = "Usage: jsWatcher.rb [options]"
  puts opts

  opts.on( '-m', '--minify', 'do minification' ) do
    DO_MIN = true
  end

  opts.on( '-w', '--watch', 'watch directory' ) do
    DO_WATCH = true
  end

  opts.on( '-p', '--poll', 'do polling' ) do
    DO_POLL = true
  end
end

optparse.parse!

# prepends needed files, e.g. jQuery.min.js or other files needed
# this happens after minification i.e. won't reminify these files
# TODO do this
def prependFiles(file, fileList)

end

# TODO
def minify(file)
  # this can be modified for greater compression
  #java -jar /bin/compiler.jar --js example.js --js_output_file example-compiled.js

  # use "--compilation_level ADVANCED_OPTIMIZATIONS" if want to maximise minificationn
  system("java -jar /bin/compiler.jar --js " + OUT_FILE + " --js_output_file " + OUT_FILE.sub(".js", ".min.js"))
end

# TODO
def gzip(file)

end

# first run through the script it checks every file

def _sanitiseDir(dir)
 return dir.gsub(/[\/]{3}|[\/]{2}/, "/")
end

# takes a file, iterates through it looking for import statements,
# appends below the import statements the recursive dependencies
# returns a file with import statements replaced with the file contents
# doesn't ensure a DAG, can give infinite loops
# always pass around the full path
def substituteContents(base, relative)

  file = base + "/" + relative
  stringFile = fileToString(file)

  matches = stringFile.scan(IMPORTRE)

  # double imports of the same file will fail
  matches.each { |m|
    idx = stringFile.index(m)
    fileName = m.match(IMPORTREFILE)[1] + ".js"
    
    newDir = _sanitiseDir(base + "/" + fileName)

    if validImport(newDir)
      stringFile.insert(idx + m.length, substituteContents(base, fileName))
    end
  }

  return stringFile
end

# returns whether the file passed in exists
def validImport(file)
  begin
    File.open(file)
    return true
  rescue
    return false
  end
end

# returns the string contents of a file
def fileToString(file)
  file = File.open(file)
  contents = ""
  file.each {|line|
    contents << line
  }
  return contents
end

# now need to create mirror structure

# also need to do the initial loop through all files and create all items

def initiateFullUpdate
  curDir = Dir.getwd()
  all = Dir['**/*.js']
  
  all.each {|jsFile|
    outFile = substituteContents(curDir, jsFile)
    # then either create or update the mirror if doesn't have an underscore
    fileName = jsFile.match(/[^|\/][\w]+\.js/)[0]

    if fileName[0,1] != "_"
      createMirror(curDir, jsFile, outFile)
    end
  }
end

# creates the mirror file, e.g. js-build/main.js -> js/main.js
def createMirror(base, relative, newFileContent)
  newDir = _sanitiseDir("/" + relative)
  splitted = newDir.split("/")
  splitted = splitted.find_all{|item| item != ""}

  cur = base + "/" + MIRROR_DIR + "/"

  splitted.each { |path|
    cur += path

    isFile = cur[-3,3] == ".js"

    if isFile
      File.open(cur, 'w') {|f| f.write(newFileContent) }
    else
      if !File.exist?(cur)
        Dir.mkdir(cur)
      end
      cur += "/"
    end
  }
end

def monitor()
  def log()
    puts "polling for *.js changes"
  end
  log()

  FSSM::Monitor.new(:directories => true)
  FSSM.monitor('.', '**/*.js', :directories => true) do

    update {|base, relative, type |
      puts relative + " changed"
      initiateFullUpdate()
      log()
    }

    create {|base, relative, type |
      puts relative + " created"
      initiateFullUpdate()
      log()
    }

    delete {|base, relative, type |
      puts relative + " deleted"
      initiateFullUpdate()
      File.delete(base + "/" + MIRROR_DIR + "/" + relative)
      log()
    }
  end
end

def main()
  if DO_POLL
    while true
      initiateFullUpdate()
      sleep(0.5)
    end
  else
    initiateFullUpdate()  
  end
  if DO_WATCH
    monitor()
  end
end

main()
