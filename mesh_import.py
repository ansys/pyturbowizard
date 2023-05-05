
def import_01(caseEl):
    if ".def" in caseEl["meshFilename"]:
        solver.file.import_.read(file_type="cfx-definition", file_name=caseEl["meshFilename"])
    elif ".msh" in caseEl["meshFilename"]:
        print("to do")
    return True
