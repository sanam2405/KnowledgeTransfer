import requests
import json
import csv
import os

def session_authentication():
	session = requests.session()

	# Retrieve the GitHub token from the environment
	GIT_TOKEN = os.environ.get("GIT_TOKEN")    

	loginUrl = "BASE_URL"
	loginHeaders = {"keys":"values"}	
	res = session.get(loginUrl, headers=loginHeaders, allow_redirects=False)
	spinnakerSession = res.cookies.get("SESSION")

	# print(spinnakerSession)
	return spinnakerSession

def getPipelineResponse(session_id,api_url):
	# API requests for getting information about the pipeline in individual applications
        application_pipeline_result = requests.get(api_url,
        headers={"keys":"values"},
        cookies={
            "SESSION": session_id,
            "keys": "values"
        },
        auth=(),
    )
        return application_pipeline_result


def getApplications(session_id):
	 # API requests for getting information about the applications
    application_result = requests.get("API_URL",
        headers={"keys":"values"},
            cookies={
                "SESSION": session_id,
                "keys": "values"
            },
            auth=(),
    )

    return application_result

def parseApplications(session_id, application_file_data, output_file_name):

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
			endpoint = "ENDPOINT_URL"

			api_url = f"{base_url}{application}{endpoint}"
			print(api_url)

			# JSON File Name
			application_pipeline_file_name = f"application_{application}_pipeline_result.json"

			threshold_requests = 0
			threshold_requests_max = 5
			isApplicationParsed = False

			while True:

				application_pipeline_result = getPipelineResponse(session_id,api_url)
				threshold_requests+=1

				# Check the response status code
				if application_pipeline_result.status_code != 200:
					session_id = session_authentication()
					continue
				else:
					try:
						# Get the response content as text
						response_text = application_pipeline_result.text

						# Save the response content as text to a JSON file
						with open(application_pipeline_file_name, 'w') as json_file:
							json_file.write(response_text)

						print(f"API response saved to {application_pipeline_file_name}")

					except Exception as e:
						print(f"Error saving API response for {application}: {str(e)}")


					print("------------------------------------------------------------------------------------------------")

					application_pipeline_file = open(application_pipeline_file_name)
					application_pipeline_data = json.load(application_pipeline_file)
					application_pipeline_file.close()

					for pipelines in application_pipeline_data:
						success = False
						if 'stages' not in pipelines:
							continue
						for stages in pipelines['stages']:
							if 'url' in stages and "validate-build" in stages['url']:
								writer.writerow({
									'Applications': applications['name'],
									'Pipelines': pipelines['name'],
									'Stage': stages['name'],
									'Scan Result': 'success',
									'End Point': 'validate-build'
								})
								success = True
							if 'url' in stages and "validate-check-runs" in stages['url']:
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

					isApplicationParsed = True

					# Check if the file exists before deleting
					if os.path.exists(application_pipeline_file_name):
						os.remove(application_pipeline_file_name)

				if isApplicationParsed == True:
					break
				if threshold_requests > threshold_requests_max:
					break


# def getApplications(session_id):    

	

def main():
	session_id = session_authentication()
	application_result = getApplications(session_id)
	application_file_name = "application_result.json"

	# Check the response status code
	if application_result.status_code == 200:

		response_text = application_result.text
		with open(application_file_name, 'w') as json_file:
			json_file.write(response_text)

		print(f"API response saved to {application_file_name}")
	
	else:
		print(f"API call failed with status code {application_result.status_code}")

	print("------------------------------------------------------------------------------------------------")

	application_file = open(application_file_name)
	application_file_data = json.load(application_file)
	application_file.close()

	output_file_name = 'spinnaker_url.csv'
	with open(output_file_name, 'w') as file:
		file.truncate(0)

	parseApplications(session_id,application_file_data,output_file_name)
	# Check if the file exists before deleting
	if os.path.exists(application_file_name):
		os.remove(application_file_name)

if __name__ == '__main__':
	main()