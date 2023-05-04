
def writeExpressionFile(locationEl, expressionEl, templateName, fileName = None):
    if fileName is None:
        fileName = "expressions.tsv"

    with open(fileName, "w") as sf:
        with open(templateName, "r") as templateFile:
            tempData = templateFile.read()
            templateFile.close()
        helperDict = locationEl
        helperDict.update(expressionEl)
        sf.write(tempData.format(**helperDict))
        sf.close()
