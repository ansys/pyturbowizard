def study(data, solver, functionName="study_01"):
    print("Running ParamatricStudy Function \"" + functionName + "\"...")
    if functionName == "study_01":
        study01(data, solver)
    else:
        print("Prescribed Function \"" + functionName + "\" not known. Skipping Parametric Study!")

    print("ParamatricStudy finished.")

def study01(studyDict, solver):
    #Init variables
    fluent_study = None
    studyIndex = 0

    for studyName in studyDict:
        studyEl = studyDict[studyName]
        # Getting all input data from json file
        datapath = studyEl.get("datapath")
        refCase = studyEl.get("refCaseFilename")

        # Read Ref Case
        #solver.file.read_case_data(file_type="case-data", file_name=refCase)
        solver.tui.file.read_case_data(refCase)

        # Initialize a new parametric study
        if fluent_study is None:
            #fluent_study = ParametricStudy(solver.parametric_studies).initialize()
            solver.parametric_studies.initialize(project_filename=studyName)
            psname = refCase + "-Solve"
            fluent_study = solver.parametric_studies[psname]

        designPointCounter = 1
        definitionList = studyEl.get("definition")

        for studyDef in definitionList:
            useScaleFactor = studyDef.get("useScaleFactor")
            ipList = studyDef.get("inputparameters")
            valueListArray = studyDef.get("valueList")
            numDPs = len(valueListArray[0])
            for dpIndex in range(numDPs):
                #new_dp = fluent_study.add_design_point()
                fluent_study.design_points.duplicate(design_point="Base DP")
                designPointName = "DP" + str(designPointCounter)
                #new_dp = {"BC_P_Out": 0.}
                new_dp = fluent_study.design_points[designPointName]
                numIPs = len(ipList)
                for ipIndex in range(numIPs):
                    ipName = ipList[ipIndex]
                    modValue = valueListArray[ipIndex][dpIndex]
                    if useScaleFactor:
                        ref_dp = fluent_study.design_points["Base DP"].input_parameters()
                        #ref_dp = {"ip1": 2.0, "BC_P_Out": 1.0, "ip3": 3.0}
                        refValue = ref_dp[ipName]
                        modValue = refValue * modValue

                    # new_dp[ipName] = modValue
                    new_dp.input_parameters = {ipName: modValue}
                    new_dp.write_data = studyEl.get("write_data")

                #fluent_study.design_points[designPointName].input_parameters = new_dp
                designPointCounter = designPointCounter + 1

        # Run all Design Points
        if studyEl["updateAllDPs"]:
            fluent_study.design_points.update_all()

        # Export results to table
        design_point_table = datapath + studyName + "_dp_table.csv"
        #fluent_study.export_design_table(design_point_table)
        solver.parametric_studies.export_design_table(filepath=design_point_table)

        # Save Study
        #solver.tui.file.parametric_project.save_as(studyName)
        if studyIndex == 0:
            solver.file.parametric_project.save()
        else:
            solver.file.parametric_project.save_as(project_filename=studyName)
        #

        if studyIndex < (len(studyDict) - 1):
            # Delete DesignPoints Current Study
            #fluent_study = fluent_study.duplicate()
            for dpIndex in range(designPointCounter - 1):
                designPointName = "DP" + str(dpIndex + 1)
                fluent_study.design_points.delete_design_points(design_points=designPointName)

        studyIndex = studyIndex + 1
    print("All Studies finished")
