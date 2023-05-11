import os.path


def writeExpressionFile(data, working_Dir):
    fileName = os.path.join(working_Dir, data["expressionFilename"])
    if fileName is None:
        fileName = "expressions.tsv"

    with open(fileName, "w") as sf:
        with open(data["expressionTemplate"], "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = data["locations"]
        helperDict.update(data["expressions"])
        sf.write(tempData.format(**helperDict))
        sf.close()
    return
