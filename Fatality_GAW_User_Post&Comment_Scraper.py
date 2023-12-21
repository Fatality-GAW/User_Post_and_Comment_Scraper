"""
    Fatality's GAW User Post and Comment Scraper
    --------------------------------------------

    This script will scrape a user's comments on https://GreatAwakening.win
    To use:
        Fill in the following variable with what you want and run it:
            USERNAME_TO_SCRAPE
        Optional variables to consider changing:
            SCRAPE_COMMENT
            SCRAPE_POST
            SAVE_DATA
    It will store the user's comments in:
        ./UserData/Username-Comments.yyyy-MM-ddTHH.mm.ss.ms.csv
        ./UserData/Username-Posts.yyyy-MM-ddTHH.mm.ss.ms.csv
    it may require you to install package:
        - beautifulsoup4

    Notes: This script was thrown together quickly, so  assumption was:
        - ignored if the comment is deleted
        - just get it working then improve as needed.
"""


import csv
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup


# Enter the username to scrape on GreatAwakening.win
USERNAME_TO_SCRAPE = 'Fatality'         # eg: this will scrape the user https://greatawakening.win/u/Fatality/
# Set at least one of these to true.
SCRAPE_COMMENT = True                   # https://greatawakening.win/u/USERNAME_TO_SCRAPE/?type=comment
SCRAPE_POST = True                      # https://greatawakening.win/u/USERNAME_TO_SCRAPE/?type=post
# Root folder to save data to:
SAVE_DATA = "./UserData"
# Comment and Post data CSV files for each user:
timenow = datetime.now().isoformat().replace(":",".")
COMMENT_DATA = f'{SAVE_DATA}/{USERNAME_TO_SCRAPE}-Comments.{timenow}.csv'
POST_DATA = f'{SAVE_DATA}/{USERNAME_TO_SCRAPE}-Posts.{timenow}.csv'


# Scrape variables (DO NOT CHANGE UNLESS THE WEBSITE CHANGES!!)
BASE_URL = 'https://GreatAwakening.win/'
USER_SUFFIX = 'u/'
COMMENT_SUFFIX = '/?type=comment'
POST_SUFFIX = '/?type=post'
SORT_SUFFIX = '&sort=new'
PAGE_SUFFIX = '&page='
PAGE_HEAD_ERROR = "Error "
PAGE_HEAD_USER_NOT_FOUND = "User Not Found "
END_OF_USER_DATA = "This user has no "



# This definition will check that the user supplied the required variables
def check_user_variables():
    problems = ''
    # Check the username:
    if USERNAME_TO_SCRAPE.strip() == '':
        problems += '- USERNAME_TO_SCRAPE variable cannot be empty.\r\n'
    # Check comment or post flag is set to True:
    if not SCRAPE_COMMENT and not SCRAPE_POST:
        problems += '- Either SCRAPE_COMMENT or SCRAPE_POST variable must be set to True.\r\n'
    # Check if output needs to be created:
    if not os.path.exists(SAVE_DATA):
        try:
            os.makedirs(SAVE_DATA)
            print("Created ", SAVE_DATA, " directory")
        except ValueError(e):
            problems += f'- {e}\r\n'
    # Check if any problems so far:
    if problems.strip() != '':
        raise ValueError(problems)


# This definition will check the user's base page to identify if they exist.
def check_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if the title of the page has "Error "
        title = soup.find('head').find('title').text
        if title.startswith(PAGE_HEAD_ERROR):
            raise ValueError(f'Invalid username: {url}')

        # Check if the title of the page has "User Not Found "
        title = soup.find('head').find('title').text
        if title.startswith(PAGE_HEAD_USER_NOT_FOUND):
            raise ValueError(f'User not found: {url}')

    except ValueError as err:
        raise ValueError(err)


# This will scrape the comments page:
def scrape_comment_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if the page content has "This user has no ":
        container = soup.find('div', {'class': 'container'})
        main = container.find('main', {'class': 'main'})
        main_content = main.find('div', {'class': 'main-content'})
        empty = main_content.find('div', {'class': 'empty'})
        if empty is not None:
            message = empty.p.get_text()
            if END_OF_USER_DATA in message:
                raise ValueError(f'User has no more comments')


        # Find all comment-list entries
        comment_list_entries = soup.find_all('div', class_='comment-list')

        # Loop through each comment-list entry
        for entry in comment_list_entries:
            # Extract Parent Post information
            parent_post_div = entry.find('div', class_='comment-parent')
            parent_post_title = parent_post_div.find('span', class_='title').a.get_text()
            parent_post_url = parent_post_div.find('span', class_='title').a['href']
            parent_post_author = parent_post_div.find('span', class_='author').a.get_text()
            parent_post_author_url = parent_post_div.find('span', class_='author').a['href']

            # Extract Comment information
            comment_div = entry.find('div', class_='comment')
            comment_body_div = comment_div.find('div', class_='body')
            comment_details_div = comment_div.find('div', class_='details')
            try: #if it doesn't get any of this data the comment is deleted:
                comment_author = comment_details_div.find('a', class_='author').get_text()
                comment_author_url = comment_details_div.find('a', class_='author')['href']
                comment_author_time = comment_details_div.find('span', class_='since').time['title']
                comment = comment_body_div.find('div', class_='content').get_text()

                # Extract Comment Actions information
                comment_actions_div = comment_div.find('div', class_='actions')
                comment_permalink = comment_actions_div.find('a', string='permalink')['href']
                comment_context = comment_actions_div.find('a', string='context')['href']
            except:
                continue #because the comment was likely deleted.
            # Return the data back
            yield [comment_author_time, comment, comment_author, comment_author_url, comment_permalink, comment_context,
                   parent_post_title, parent_post_url, parent_post_author, parent_post_author_url]
    except ValueError as e:
        raise ValueError(e)


# This will scrape the posts page:
def scrape_post_page(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Check if the page content has "This user has no ":
        container = soup.find('div', {'class': 'container'})
        main = container.find('main', {'class': 'main'})
        main_content = main.find('div', {'class': 'main-content'})
        empty = main_content.find('div', {'class': 'empty'})
        if empty is not None:
            message = empty.p.get_text()
            if END_OF_USER_DATA in message:
                raise ValueError(f'User has no more Posts')

        # Find all comment-list entries
        post_list_entries = soup.find_all('div', class_='post-list')

        # Loop through each post-list entry
        for entry in post_list_entries:
            # Extract the Post information
            post_div = entry.find('div', class_='body')
            post_title = post_div.find('div', class_='top').a.get_text()
            post_url = post_div.find('div', class_='top').a['href']
            post_time = post_div.find('span', class_='since').time['title']
            post_author = post_div.find('span', class_='since').a.get_text()
            author_url = post_div.find('span', class_='since').a['href']
            # Return the data back
            yield [post_time, post_title, post_url, post_author, author_url]
    except ValueError as e:
        raise ValueError(e)


# This method will scrape as many pages as the user has.
def scrape_user_data(username):
    page_number = 1

    base_user_url = f'{BASE_URL}{USER_SUFFIX}{username}'

    # Make sure the username exists:
    try:
        check_page (base_user_url)
        print(f'Valid username: {base_user_url}')
    except ValueError as e:
        raise ValueError(e)

    # Initialize comment and post data:
    comment_data = []
    post_data = []
    global SCRAPE_COMMENT
    global SCRAPE_POST

    # Gather all the Comment & Post data:
    while SCRAPE_COMMENT or SCRAPE_POST:

        if SCRAPE_COMMENT:
            user_page_url = f'{base_user_url}{COMMENT_SUFFIX}{SORT_SUFFIX}{PAGE_SUFFIX}{page_number}'
            print(f'Scraping {username}\'s comments page {page_number} @ {user_page_url}')
            try:
                for comment in scrape_comment_page(user_page_url):
                    comment_data.append(comment)
            except ValueError as e:
                print('-'*50)
                print(e)
                print('-' * 50)
                SCRAPE_COMMENT = False

        if SCRAPE_POST:
            user_page_url = f'{base_user_url}{POST_SUFFIX}{SORT_SUFFIX}{PAGE_SUFFIX}{page_number}'
            print(f'Scraping {username}\'s posts page {page_number} @ {user_page_url}')
            try:
                for post in scrape_post_page(user_page_url):
                    post_data.append(post)
            except ValueError as e:
                print('-' * 50)
                print(e)
                print('-' * 50)
                SCRAPE_POST = False

        page_number += 1

    # Write the comment data to a CSV file
    with open(COMMENT_DATA, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Comment_Time', 'Comment', 'Comment_Author', 'Comment_Author_URL',
                         'Comment_PermaLink', 'Comment_Context', 'Parent_Post_Title', 'Parent_Post_URL',
                         'Parent_Post_Author', 'Parent_Post_Author_URL'])
        writer.writerows(comment_data)

    # Write the post data to a CSV file
    with open(POST_DATA, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Post_Time', 'Post_Title', 'Post_URL', 'Post_Author', 'Author_URL'])
        writer.writerows(post_data)


# The main program:
try:
    check_user_variables()
except ValueError as e:
    print(e)
    quit()

try:
    scrape_user_data(USERNAME_TO_SCRAPE)
except ValueError as e:
    print(e)
    quit()
