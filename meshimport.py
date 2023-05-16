

def import_01(data, solver):
    success = False
    meshFilename = data["meshFilename"]
    if meshFilename.endswith(".def") or meshFilename.endswith(".cgns"):
        solver.file.import_.read(file_type="cfx-definition", file_name = meshFilename)
        success = True
    else:
        solver.file.read_case(file_type="case", file_name = meshFilename)
        success = True

    # BC Profiles
    profileName = data.get("profileName")
    if profileName is not None:
        solver.file.read_profile(file_name=profileName)

    return success
