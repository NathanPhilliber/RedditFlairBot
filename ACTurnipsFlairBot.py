
import praw
import time
import re
import imaplib
import email
import smtplib

mail = None
server = None

r = None

file = None

mainLoop = True

r = praw.Reddit("ACTurnips Flair Bot")
r.login("USERNAME", "PASSWORD")
msg = "Hello, "
modMsg = ""
rateUrl = ""
oldAuthors = []

def friendCodeIsValid(code):
    code = str(code)
    
    codeClean = filter(str.isdigit, code)
    
    if len(codeClean) != 12:
        return False
    
    return True

def formatFriendCode(code):
    code = str(code)
    codeClean = filter(str.isdigit, code)
    code = codeClean[:4] + "-" + codeClean[4:]
    code = code[:9] + "-" + code[9:]
    
    return code

def checkSpecial(flairCur):
	if flairCur == "Blue":
		return Flase
	if flairCur == "Purple":
		return False
	if flairCur == "Orange":
		return False
	if flairCur == "Pink":
		return False	
	if flairCur == "Red":
		return False
	if flairCur == "Yellow":
		return False
	if flairCur == "White":
		return False
	return True

def setupIMAP():
    global mail, server
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login("USER@gmail.com", "PASSWORD")
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login("USER@gmail.com", "PASSWORD")
    
def findEmail():
    global mail
    
    emailKey = "1337"
    maxSearches = 5
    
    mail.list()
    mail.select("inbox")

    result, data = mail.search(None, "ALL")

    ids = data[0]
    id_list = ids.split()
    
    if len(id_list) < 5:
        maxSearches = len(id_list)
    latest_email_id = id_list[-1]
    ##print >>file, id_list
    
    current = 0
    while(current < maxSearches):
        
        result, data = mail.fetch(id_list[len(id_list)-1-current], "(RFC822)")
        raw_email = data[0][1]
    
        xyz = email.message_from_string(raw_email)
    
        if xyz.get_content_maintype() == 'multipart': #If message is multi part we only want the text version of the body, this walks the message and gets the body.
            for part in xyz.walk():       
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True)
                else:
                    continue
                     
        if body.find(emailKey) >= 0:
	    
	    mail.store(len(id_list)-current, '+FLAGS', '\\Deleted')
	    mail.expunge()
	    returnString = body.replace(emailKey + " ","",1)
	    ##print >>file, returnString
            return returnString
    
        current += 1
    return ""
def getTurnipColor(num):
    
    num = int(num)
    
    if num >= 200:
        return "Blue"
    if num >= 100:
        return "Purple"
    if num >= 50:
        return "Orange"
    if num >= 25:
        return "Pink"
    if num >= 10:
        return "Red"
    if num >= 5:
        return "Yellow"
    else:
        return "White"
#Start Program
setupIMAP()
while mainLoop:
    file = open("ACoutput.txt", "a")
    r.login("USERNAME", "PASSWORD")
    #setupIMAP()
    subreddit = r.get_subreddit('ratemymayor')
    acturnipsSub = r.get_subreddit("acturnips")
    mods = r.get_moderators(subreddit)
    del oldAuthors[:]
    for message in r.get_unread():
        
        author = message.author.name
        
        if author in oldAuthors:
            message.mark_as_read()
            #print >>file, "Duplicate message from " + author + ", skipping..."
        else:
            oldAuthors.append(author)
            msg += author
            msg += ". I am a bot. It looks like you requested a "
            print "Updating for " + message.author.name
            if message.subject == "1":
                
                msg += "full information update. "

                information = re.split(",~,", message.body)
                
                if len(information) == 3:
                    townName = information[0]
                    friendCode = information[1]
                    mayorName = information[2]
                    
                    if friendCodeIsValid(friendCode):
			
			friendCode = formatFriendCode(friendCode)

                        anything = False
			
                        for ratePage in r.search(author, subreddit, sort = 'new'):
                            if ratePage.author.name == "RateMyMayor" and ratePage.title.lower() == author.lower():
                                rateUrl = ratePage.url
                                anything = True
                                #print >>file, "\tFound RateMyMayorPage"
                                high = 0
                                cur = 0
                                comCount = 0
                                for comment in ratePage.comments:
                                    comCount += 1
                                    if comment.author in mods and comment.body.find("/5") < 0:
                                        comCount -= 1
                                        cur = re.search(r'\d+', comment.body).group()
                                        if cur != "":
					    cur = str(cur)
				    
					    cur = int(cur)
					    if cur > high:
						high = cur

                                flairRaw = acturnipsSub.get_flair(author)
                            
                                flairClass = flairRaw["flair_css_class"]
                                flairText = flairRaw["flair_text"]
                                
                                
                                if str(flairClass) == "None" or flairClass == "":
					flairClass = "White"

                                elif checkSpecial(flairClass):

				    msg += "And it looks like you have a special flair. I cannot update this so I have sent a human moderator your turnip request. Expect an update within 1-2 days. Have a great day!"
                                    modMsg += "Hello Humans. It looks like /u/" + author + " is trying to update their turnip color. Unfortunately, they have a special flair: " + flairClass + " , so I cannot upgrade them. [Here's their RMM page](" + rateUrl + "). Thanks!"
                                    r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                                    r.get_subreddit("acturnips").set_flair(author, friendCode + " - " + mayorName + ", " + townName, str(flairClass))
                                else:
                                    if (getTurnipColor(comCount) != getTurnipColor(high) and int(high) - comCount > -1): #remove second check??
					#print >>file, "\tUsers current flair is too high compared to RMM page"
					msg += "Your turnip has been updated to "
					msg += getTurnipColor(high)
					msg += ". Just so you know, I have already contacted the moderators because there may be something wrong with your RMM page or my counting, although this could be due to having two RMM pages. "
					modMsg += "Hello Humans. It looks like /u/" + author + " may need some assistance setting their flair. This person might have two pages or something but according to their RMM page they shouldn't have their current flair. [Here's their RMM page](" + rateUrl + "), I have set their flair to: " + getTurnipColor(high) + ". [Here's the edit flair link](http://www.reddit.com/r/acturnips/about/flair/?name=" + author + ") Thanks!"
					r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                                
                                    if getTurnipColor(comCount) != getTurnipColor(high) and comCount - int(high) > -1:
					
                                        msg += "Whoa! It looks like you might be due for a new turnip color! I have already sent a message to a human moderator to see if this is correct. If you do indeed qualify for a new turnip color, expect the change within a day or two. "
                                        modMsg +="Hello Humans. It looks like /u/" + author + " may need a recount on their /r/RateMyMayor page. [Here's the link](" + rateUrl + ") to their RMM page. Their town name is **" + townName + "** their character name is **" + mayorName + "** and their friendCode is **" + friendCode + "**. Thanks Guys!"
                                        r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                                        #print >>file, "\tSent messages to mods for recount"
                                    r.get_subreddit("acturnips").set_flair(author, friendCode + " - " + mayorName + ", " + townName, getTurnipColor(high))
				    msg += "All of your information appears to be correct and your turnip is currently "
                                    msg += getTurnipColor(high)
                                    msg += ". Have a great day!"
                                #print >>file, "\tSuccess"
                                
                                break
                        if anything == False:
                            #print >>file, "\tNo RMM page found"
                            msg += "Unfortunately, I could not find a /r/RateMyMayor page for you. Do you have one? If you don't why not make one? If you do have a page already and believe this error is on my part, please [message the mods](http://www.reddit.com/message/compose?to=%2Fr%2Facturnips), please include this message in your report. Regardless, your information has been updated. Thank you! Have a great day."
                            
                            flairRaw = acturnipsSub.get_flair(author)
                            ##print >>file, flairRaw
                            flairClass = flairRaw["flair_css_class"]
                            flairText = flairRaw["flair_text"]
                            ##print >>file, flairClass
			    if str(flairClass) == "None":
				flairClass = "White"
				#print >>file, "\tSetting flair to white"
			    
                            acturnipsSub.set_flair(author, friendCode + " [" + mayorName + " - " + townName + "]", str(flairClass))
			    
                    else:
                        #print >>file, "\tFriend code is not in right format"
                        msg += "Unfortunately, your friend code is invalid. Is it in the right format? 0000-0000-0000 If you believe this to be an error please [message the mods](http://www.reddit.com/message/compose?to=%2Fr%2Facturnips) or try to resend the form with your friendcode in the correct format. Have a great day!"
                    
                else:
                    #print >>file, "Too many arguments: " + len(information)
                    msg += "Unfortunately, I could not update your flair because the message format was incorrect. Did you tamper with the message that was generated for me? Please try to resend the tumblr form, or if you believe this to be an error, [message the mods](http://www.reddit.com/message/compose?to=%2Fr%2Facturnips). Please include this message in your message. Have a great day!"
            elif message.subject == "2":
                #Check rate my mayor now
                msg += "turnip color update. "
                #print >>file, "Updating turnip only for: " + author
                #print >>file, (time.strftime("%I:%M:%S"))
                #print >>file, (time.strftime("%d/%m/%Y"))
                anything = False
                
                for ratePage in r.search(author, subreddit, sort='new'):
                    if ratePage.author.name == "RateMyMayor" and ratePage.title.lower() == author.lower():
                        rateUrl = ratePage.url
                        anything = True
                        #print >>file, "\tFound RateMyMayorPage"
                        high = 0
                        cur = 0
                        comCount = 0
                        for comment in ratePage.comments:
                            comCount += 1
                            if comment.author in mods and comment.body.find("/5") < 0:
                                comCount -= 1
                                cur = re.search(r'\d+', comment.body).group()
				
				
				if cur != "":
				    cur = str(cur)
				    
				    cur = int(cur)
				    if cur > high:
					high = cur
				    #print >>file, "\t-" + comment.author.name + " " + str(cur)
                        
                        #print >>file, "\tHighest count: " + str(high)
                        #print >>file, "\tFlair = " + getTurnipColor(int(high))
                        
                        flairRaw = acturnipsSub.get_flair(author)
                        
                        flairClass = flairRaw["flair_css_class"]
                        flairText = flairRaw["flair_text"]
                        if str(flairClass) == "None" or flairClass == "":
				flairClass = "White"
				#print >>file, "\tSetting flair to white"
                        elif checkSpecial(str(flairClass)):
                            #print >>file, "\tUser has special flair already!"
                            
                            msg += "And it looks like you have a special flair. I cannot update this so I have sent a human moderator your turnip request. Expect an update within 1-2 days"
                            
                            modMsg += "Hello Humans. It looks like /u/" + author + " is trying to update their turnip color. Unfortunately, they have a special flair: " + flairClass + " , so I cannot upgrade them. [Here's their RMM page](" + rateUrl + "). Thanks!"
                            r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                        else:
                            if getTurnipColor(comCount) != getTurnipColor(high) and int(high) - comCount > -1:
                                #print >>file, "\tUsers current flair is too high compared to RMM page"
				msg += "Your turnip has been updated to "
				msg += getTurnipColor(high)
				msg += ". Just so you know, I have already contacted the moderators because there may be something wrong with your RMM page or my counting, although this could be due to having two RMM pages. "
                                modMsg += "Hello Humans. It looks like /u/" + author + " may need some assistance setting their flair. This person might have two pages or something but according to their RMM page they shouldn't have their current flair. [Here's their RMM page](" + rateUrl + "), I have set their flair to: " + getTurnipColor(high) + ". [Here's the edit flair link](http://www.reddit.com/r/acturnips/about/flair/?name=" + author + ") Thanks!"
                                r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                                
                            if getTurnipColor(comCount) != getTurnipColor(high) and comCount - int(high) > -1:
                                
                                
                                msg += "Whoa! It looks like you might be due for a new turnip color! I have already sent a message to a human moderator to see if this is correct. If you do indeed qualify for a new turnip color, expect the change within a day or two. "
                            
                                modMsg +="Hello Humans. It looks like /u/" + author + " may need a recount on their /r/RateMyMayor page. [Here's the link](" + rateUrl + ") to their RMM page. Thanks!"
                                
                                r.send_message(acturnipsSub, "Possible RMM Recount", modMsg)
                                #print >>file, "\tSent message to mods for recount"
                                
                                msg += "Everything seems to be in order. Your turnip is currently "
                                msg += getTurnipColor(high)
				msg += ". "
                
                            r.get_subreddit("acturnips").set_flair(author, str(flairText), getTurnipColor(high))
                        msg += "Have a great day!"
                        #print >>file, "Success"
                        break
                
                if anything == False:
                    #print >>file, "\tCould not find a mayor page for " + author
                    flairRaw = acturnipsSub.get_flair(author)
		    ##print >>file, flairRaw
		    flairClass = flairRaw["flair_css_class"]
		    flairText = flairRaw["flair_text"]
		    ##print >>file, flairClass
		    if str(flairClass) == "None":
		        flairClass = "White"
		        #print >>file, "\tSetting flair to white"
		    
		    acturnipsSub.set_flair(author, str(flairText), str(flairClass))
		    msg += "Unfortunately, I could not find a /r/RateMyMayor page for you. Do you have one? If you don't why not make one? If you do have a page already and believe this error is on my part, please [message the mods](http://www.reddit.com/message/compose?to=%2Fr%2Facturnips), please include this message in your report. Thank you! Have a great day."
            else:
                msg += "UNKNOWN UPDATE TYPE. Unfortunately, I do not know what you're trying to do, did you tamper with the message that was generated for me? If you think that I am mistaken, please [message the mods](http://www.reddit.com/message/compose?to=%2Fr%2Facturnips). Thank you! Have a great day."
                #print >>file, "\tUnknown subject ID"    
            #send author the msg
            r.send_message(author, "ACTurnips Flair Update", msg)
	    msg = "Hello, "
	    modMsg = ""
            message.mark_as_read()
            
    #mainLoop = False #DEBUG ONLY
    #print >>file, "Checking for email commands..."
    cmd = findEmail()
    if cmd == "stop":
	mainLoop = False
	#print >>file, "Stopping program..."
	server.sendmail("ACTurnips", "6507738488@vtext.com", "Stopping Bot")
	#print >>file, (time.strftime("%I:%M:%S"))
        #print >>file, (time.strftime("%d/%m/%Y"))
	break
    elif cmd == "info":
	#print >>file, "Requested Info"
	server.sendmail("ACTurnips", "6507738488@vtext.com", "I'm still running")
    cmd = ""	
    #print >>file, "Sleeping for 300 seconds"
    print "Sleeping for 300 seconds"
    file.close()
    time.sleep(300)
    ##print >>file, "Done sleeping, starting new cycle"
    print "Done, starting new cycle"
    