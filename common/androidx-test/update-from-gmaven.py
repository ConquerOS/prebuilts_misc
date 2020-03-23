#!/usr/bin/python3

# Helper script for updating androidx.test prebuilts from maven
#
# Usage:
#   a. Initialize android environment eg . build/envsetup.sh; lunch <target>
#   b. Update the version numbers in this file
#   c. ./prebuilts/misc/androidx-test/update-from-gmaven.py
#
# The script will then:
#   1. Remove the previous artifacts
#   2. Download the aars and poms into a file structure mirroring their maven
#      path
#   3. Extract the AndroidManifest from the aars into the manifests folder
#   4. Run pom2bp to generate the Android.bp

import os
import subprocess
import sys

runnerVersion="1.3.0-alpha05"
rulesVersion=runnerVersion
espressoVersion="3.3.0-alpha05"
coreVersion=runnerVersion
extJUnitVersion="1.1.2-alpha05"
extTruthVersion=runnerVersion
jankTestHelperVersion="1.0.1"
uiAutomatorVersion="2.2.0"

mavenToBpPatternMap = {
    "androidx.test:" : "androidx.test.",
    "androidx.test.ext:": "androidx.test.ext.",
    "androidx.test.espresso:espresso-":"androidx.test.espresso.",
    "androidx.test.janktesthelper:janktesthelper":"androidx.test.janktesthelper",
    "androidx.test.uiautomator:uiautomator":"androidx.test.uiautomator",
    }

extraLibs = {
    "androidx.test.rules" : "android.test.base",
    "androidx.test.uiautomator" : "android.test.base",
    }

def cmd(args):
   print(args)
   out = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
   if (out.returncode != 0):
      print(out.stderr.decode("utf-8"))
      sys.exit(out.returncode)
   out_string = out.stdout.decode("utf-8")
   print(out_string)
   return out_string

def chdir(path):
   print("cd %s" % path)
   os.chdir(path)

def getAndroidRoot():
   if os.path.isdir(".repo/projects"):
      return os.getcwd()
   elif 'TOP' in os.environ:
      return os.environ['TOP']
   else:
      print("Error: Run from android source root or set TOP envvar")
      sys.exit(-1)

def downloadArtifact(groupId, artifactId, version):
   """Downloads an aar, sources.jar and pom from google maven"""
   groupPath = groupId.replace('.', '/')
   artifactDirPath = os.path.join(groupPath, artifactId, version)
   artifactPath = os.path.join(artifactDirPath, "%s-%s" % (artifactId, version))
   cmd("mkdir -p " + artifactDirPath)
   # download aar
   cmd("wget -O %s.aar https://dl.google.com/dl/android/maven2/%s.aar" % (artifactPath, artifactPath))

   # extract AndroidManifest.xml from aar, into path expected by pom2bp
   manifestDir = getManifestPath("%s:%s" % (groupId,artifactId))
   cmd("mkdir -p " + manifestDir)
   cmd("unzip -o %s.aar AndroidManifest.xml -d %s" % (artifactPath, manifestDir))

   # download pom
   cmd("wget -O %s.pom https://dl.google.com/dl/android/maven2/%s.pom" % (artifactPath, artifactPath))
 
   # download sources.jar
   cmd("wget -O %s-sources.jar https://dl.google.com/dl/android/maven2/%s-sources.jar" % (artifactPath, artifactPath))


def getManifestPath(mavenArtifactName):
  """Get the path to the aar's manifest as generated by pom2bp."""
  manifestPath = mavenArtifactName
  for searchPattern in mavenToBpPatternMap:
    manifestPath = manifestPath.replace(searchPattern, mavenToBpPatternMap[searchPattern])
  return "manifests/%s" % manifestPath

prebuiltDir = os.path.join(getAndroidRoot(), "prebuilts/misc/common/androidx-test")
chdir(prebuiltDir)

cmd("rm -rf androidx/test")
cmd("rm -rf manifests")

downloadArtifact("androidx.test", "core", coreVersion)
downloadArtifact("androidx.test.espresso", "espresso-core", espressoVersion)
downloadArtifact("androidx.test.espresso", "espresso-contrib", espressoVersion)
downloadArtifact("androidx.test.espresso", "espresso-idling-resource", espressoVersion)
downloadArtifact("androidx.test.espresso", "espresso-intents", espressoVersion)
downloadArtifact("androidx.test.espresso", "espresso-idling-resource", espressoVersion)
downloadArtifact("androidx.test.espresso", "espresso-web", espressoVersion)
downloadArtifact("androidx.test", "monitor", runnerVersion)
downloadArtifact("androidx.test", "rules", rulesVersion)
downloadArtifact("androidx.test", "runner", runnerVersion)
downloadArtifact("androidx.test.ext", "junit", extJUnitVersion)
downloadArtifact("androidx.test.ext", "truth", extTruthVersion)
downloadArtifact("androidx.test.janktesthelper", "janktesthelper", jankTestHelperVersion)
downloadArtifact("androidx.test.uiautomator", "uiautomator", uiAutomatorVersion)

atxRewriteStr = ""
for name in mavenToBpPatternMap:
  atxRewriteStr += "-rewrite %s=%s " % (name, mavenToBpPatternMap[name])
for name in extraLibs:
  atxRewriteStr += "-extra-libs %s=%s " % (name, extraLibs[name])

cmd("pom2bp " + atxRewriteStr +
    # map external maven dependencies to Android module names
    "-rewrite com.google.truth:truth=truth-prebuilt " +
    "-rewrite net.sf.kxml:kxml2=kxml2-android " +
    "-rewrite androidx.lifecycle:lifecycle-common=androidx.lifecycle_lifecycle-common " +
    "-rewrite androidx.annotation:annotation=androidx.annotation_annotation " +
    "-rewrite org.hamcrest:hamcrest-integration=hamcrest " +
    "-rewrite javax.inject:javax.inject=jsr330 " +
    "-rewrite com.google.android.material:material=com.google.android.material_material " +
    "-rewrite androidx.drawerlayout:drawerlayout=androidx.drawerlayout_drawerlayout " +
    "-rewrite androidx.viewpager:viewpager=androidx.viewpager_viewpager " +
    "-rewrite androidx.recyclerview:recyclerview=androidx.recyclerview_recyclerview " +
    "-rewrite androidx.core:core=androidx.core_core " +
    "-rewrite androidx.legacy:legacy-support-core-utils=androidx.legacy_legacy-support-core-utils " +
    "-sdk-version current " +
    "-static-deps " +
    ". > Android.bp")
