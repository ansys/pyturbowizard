

def import_01(data, solver):
    success = False
    print("test")
    if ".def" in data["meshFilename"]:
        solver.file.import_.read(file_type="cfx-definition", file_name=data["meshFilename"])
        success = True


    # BC Profiles
    solver.file.read_profile(file_name=data["profileName"])

    return success
