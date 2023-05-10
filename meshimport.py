

def import_01(data, solver):
    success = False
    meshFilename = data["meshFilename"]
    if meshFilename.endswith(".def") or meshFilename.endswith(".cgns"):
        solver.file.import_.read(file_type="cfx-definition", file_name = meshFilename)
        success = True
    else:
        solver.file.read_case_data(file_type="case", file_name = meshFilename)
        success = True

    # BC Profiles
    solver.file.read_profile(file_name=data["profileName"])

    return success
