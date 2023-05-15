import os.path


def writeExpressionFile(data, working_dir):
    fileName = os.path.join(working_dir, data["expressionFilename"])
    if fileName is None:
        fileName = "expressions.tsv"

    with open(fileName, "w") as sf:
        with open(data["expressionTemplate"], "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        expressionEl = data.get("expressions")
        helperDict.update(expressionEl)
        tempData = cleanupInputExpressions(expressionEl=expressionEl, fileData=tempData)
        sf.write(tempData.format(**helperDict))
        sf.close()
    return
def cleanupInputExpressions(expressionEl: dict, fileData:str):
    cleanfiledata = ""
    for line in fileData.splitlines():
        #write header line
        if cleanfiledata == "":
            cleanfiledata = line
        #check BCs and prescribed Expressions
        elif line.startswith("\"BC"):
            for expKey in expressionEl:
                if expKey in line:
                    cleanfiledata = cleanfiledata + "\n" + line
                    break
        else:
            cleanfiledata = cleanfiledata + "\n" + line

    return cleanfiledata



