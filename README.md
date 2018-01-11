# sntool
User level utility for dealing with StorNext filesystem

The utility was created a couple of years ago when we were using StorNext because 
StorNext did not have user level commands to check, retrieve or archive files.
Inevitably there are a few things related to file system which are specific to our setup.
Specifically, we had two mirror sites A and B and some files were located on A and others on B.
Also our file system structure had major division on long term storage (lt) and short term storage (st)
which was reflected in the mounts.

Using the tool, a user would execute it on a file name using relative or absolute path.
The tool would then figure out where the file is located and perform a query or an action.
Unfortunately StorNext sends the query using plain text password.
To obfuscate the password, it was converted to URL encoding and furthermore the tool
was distributed in a binary form rather than plain text Python code.
There were also tests but they are excluded as site specific.

In order to adapt the tool to your environment you need to change a couple of things in the main Python script.
First of all note, that the script assumes that StoreNext is mounted under /data/ like this:
```
/data/
/data/aaalt
/data/aaast
/data/bbblt
/data/bbbst
```
Change the IP addresses:
```
# base URLs
urla = "http://12.34.56.78:81/axis2/services/stornext/"
urlb = "http://12.34.56.79:81/axis2/services/stornext/"
```
Remove, change or adapt your sites:
```
    if   sname[1:4] == "aaa":
        url = urla
    elif sname[1:4] == "bbb":
        url = urlb
```
