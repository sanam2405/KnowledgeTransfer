import requests
import json
import csv
import os

def session_authentication():
    session = requests.session()

    # Retrieve the GitHub token from the environment
    GIT_TOKEN = os.environ.get("GIT_TOKEN")    

    loginUrl = "LOGIN_URL"
    loginHeaders = {"keys":"values"}
    res = session.get(loginUrl, headers=loginHeaders, allow_redirects=False)
    spinnakerSession = res.cookies.get("SESSION")

    # print(spinnakerSession)
    return spinnakerSession

def parseApplications(application_file_data, output_file_name):


    # Check if the file is present
    if os.path.isfile(output_file_name):
        # Check if the file is empty
        is_file_empty = (os.stat(output_file_name).st_size == 0)
    else:
        # File does not exist
        is_file_empty = True

    # Create and open the CSV file in write mode
    with open(output_file_name, 'a', newline='') as csvfile:
        fieldnames = ['Applications','Pipelines', 'Stage', 'Scan Result', 'End Point']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the column names to the CSV file
        if is_file_empty:
            writer.writeheader()


        for applications in application_file_data:

            print(applications['name'])

            base_url = "BASE_URL"
            application = applications['name']
            endpoint = "/END_POINT"

            api_url = f"{base_url}{application}{endpoint}"
            print(api_url)

            # JSON File Name
            application_pipeline_file_name = f"application_{application}_pipeline_result.json"



            # API requests for getting information about the pipeline in individual applications
            application_pipeline_result = requests.get(api_url,
            headers={"keys":"values"},
            cookies={
                "SESSION": session_authentication(),
                "keys": "values"
            },
            auth=(),
        )

            # Check the response status code
            if application_pipeline_result.status_code == 200:
                try:
                    # Get the response content as text
                    response_text = application_pipeline_result.text

                    # Save the response content as text to a JSON file
                    with open(application_pipeline_file_name, 'w') as json_file:
                        json_file.write(response_text)

                    print(f"API response saved to {application_pipeline_file_name}")

                except Exception as e:
                    print(f"Error saving API response for {application}: {str(e)}")

            else:
                print(f"API call for {application} failed with status code {application_pipeline_result.status_code}")

            print("------------------------------------------------------------------------------------------------")

            application_pipeline_file = open(application_pipeline_file_name)
            application_pipeline_data = json.load(application_pipeline_file)
            application_pipeline_file.close()



            for pipelines in application_pipeline_data:
                success = False
                for stages in pipelines['stages']:
                    if 'url' in stages['context'] and "validate-build" in stages['context']['url']:
                        writer.writerow({
                            'Applications': applications['name'],
                            'Pipelines': pipelines['name'],
                            'Stage': stages['name'],
                            'Scan Result': 'success',
                            'End Point': 'validate-build'
                        })
                        success = True
                    if 'url' in stages['context'] and "validate-check-runs" in stages['context']['url']:
                        writer.writerow({
                            'Applications': applications['name'],
                            'Pipelines': pipelines['name'],
                            'Stage': stages['name'],
                            'Scan Result': 'success',
                            'End Point': 'validate-check-runs'
                        })
                        success = True

                if not success:
                    writer.writerow({
                        'Applications': applications['name'],
                        'Pipelines': pipelines['name'],
                        'Stage': 'NA',
                        'Scan Result': 'failure',
                        'End Point': 'NA'
                    })

            # Check if the file exists before deleting
            if os.path.exists(application_pipeline_file_name):
                os.remove(application_pipeline_file_name)


# x----------------------------------------------------------------------------------------------------------------------------x
# x----------------------------------------------------------------------------------------------------------------------------x

def getApplications():

    # API requests for getting information about the applications
    application_result = requests.get("API_URL",
        headers={"keys":"values"},
            cookies={
                "SESSION": session_authentication(),
                "keys": "values"
            },
            auth=(),
    )

    application_file_name = "application_result.json"

    # Check the response status code
    if application_result.status_code == 200:
        try:
            # Get the response content as text
            response_text = application_result.text

            # Save the response content as text to a JSON file
            with open(application_file_name, 'w') as json_file:
                json_file.write(response_text)

            print(f"API response saved to {application_file_name}")

        except Exception as e:
            print(f"Error saving API response: {str(e)}")

    else:
        print(f"API call failed with status code {application_result.status_code}")

    print("------------------------------------------------------------------------------------------------")

    application_file = open(application_file_name)
    application_file_data = json.load(application_file)
    application_file.close()

    output_file_name = 'spannaker.csv'
    with open(output_file_name, 'w') as file:
        file.truncate(0)

    parseApplications(application_file_data,output_file_name)
    # Check if the file exists before deleting
    if os.path.exists(application_file_name):
        os.remove(application_file_name)

def main():
    getApplications()

if __name__ == '__main__':
    main()
