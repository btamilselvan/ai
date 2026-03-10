import re
text = """
 Yes, there is a Butter Chicken recipe available in the system! I found one recipe with ID 10973 
 titled "Butter Chicken."\n\nTo provide you with the full recipe details including ingredients, 
 instructions, and cooking steps, I would need to access the complete recipe resource. 
 However, I\'m currently unable to retrieve the full content 
 from the resource URI `recipe://details/10973` as that functionality isn\'t available to me at the moment.\n\nWould you like me to help you with any other recipe searches or provide guidance on what you\'d like to know about Butter Chicken recipes?
"""

pattern = r"recipe://details/(\d+)"

matches = re.finditer(pattern, text)
matches = list(matches)
if(len(matches) > 0):
    match = matches[0]
    print(match.group(0))
# if len(list(matches)) > 0:
#     print("found")

for match in matches:
    full_uri = match.group(0)  # The whole string: recipe://details/1234
    recipe_id = match.group(1) # Just the digits: 1234
    
    print(f"Found URI: {full_uri} | ID to process: {recipe_id}")

# print(f"Fetching resource: {resource_uri}")
