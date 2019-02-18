#!/usr/bin/python

import argparse
import sys
import os
import boto.cloudformation
import boto3
import requests
import time

boto3.setup_default_session(profile_name='b')

conn = boto.cloudformation.connection.CloudFormationConnection()
cloudformation = boto3.resource('cloudformation')
conn3 = boto3.client('cloudformation')
s3 = boto3.resource('s3')
parser=argparse.ArgumentParser(description="Test")
parser.add_argument("-a","--add",nargs="+",help="Add a stack")
parser.add_argument("-d","--dele",nargs="+",help="Delete a stack")
parser.add_argument("-l","--list",nargs="+",help="List a stack")
parser.add_argument("-u","--update",nargs="+",help="Update a stack")
parser.add_argument("-t","--test",help="Test ELB",action='store_true')
parser.add_argument("-p","--parse",help="Parse template",action='store_true')
parser.add_argument("-e","--elb",nargs="+",help="ELB Instance Check")
parser.add_argument("-c","--copy",help="Upload CF template to S3 Bucket",action='store_true')
args=parser.parse_args()

def test_iam_creds():
	try:
		client = boto3.client('iam')
		response = client.list_users()
		return True
	except Exception as e:
#		print(str(e)+'\n')
		return False
def parse():
	try:
		conn3.validate_template(TemplateURL='https://s3.amazonaws.com/cf-template-krishna/CF_Template.json')
		print("\nThe template valdation is successful\n")
	except Exception as e:
		print("\nOOPS! An error occured while processing the request!")
                print(str(e)+'\n')
def updatestack(j):
                try:
			copy()
			print('Fetching the file....')
			print j
                        conn3.update_stack(StackName=j,TemplateURL='https://s3.amazonaws.com/cf-template-krishna/CF_Template.json',UsePreviousTemplate=False)
                        print("\nInitiating the Stack updation of "+j+"\n")
			time.sleep(10)
			liststack(j)
                except Exception as e:
			print("\nOOPS! An error occured while processing the request!")
                	print(str(e)+'\n')
def createstack(j):
        try:
		conn.create_stack(j, template_body=None, template_url='https://s3.amazonaws.com/krishna-new/NewCF-WithNAT.json',  notification_arns=[])
                print("\nReading the Cloud Formation template from https://s3.amazonaws.com/krishna-new/NewCF-WithNAT.json")
		print("\nInitiating the Stack creation of "+j+"..Check the output section of the stack to see the resources created!")
 		time.sleep(10)
		liststack(j)
        except Exception as e:
		print("\nOOPS! An error occured while processing the request!")
                print(str(e)+'\n')
def liststack(j):
        try:
		response = conn3.describe_stack_resources(StackName=j)
		print("|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|")
		print('|'+'\t'+"ResourceType                                 PhysicalResourceId                     LogicalResourceId                         Resource Status"+'                       |')
		print("|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|")
		for j in range(0,len(response['StackResources'])):
        		p=response['StackResources'][j]['PhysicalResourceId']
        		r=response['StackResources'][j]['ResourceType']
        		rs=response['StackResources'][j]['ResourceStatus']
        		l=response['StackResources'][j]['LogicalResourceId']
        		print('|'+'\t'+'{}'.format(r).ljust(45) + '{}'.format(p).ljust(40)+'{}'.format(l).ljust(40)+'{}'.format(rs).ljust(39)+'|')
		print("|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------|")
	
        except Exception as e:
                print("\nOOPS! An error occured while processing the request!")
		print(str(e)+'\n')

def delstack(j):
		check = "Stack with id "+str(args.dele[0])+" does not exist"
                value= ""
                try:
                        conn.describe_stacks(stack_name_or_id=args.dele[0])
                except Exception as e:
                        value=e.error_message
                if value==check:
                            print ("\nThere is no stack named:"+args.dele[0]+" to delete!!!\n")
		else:
                	print("\nYou are about to delete the stack:"+j+". Please confirm if you really want to delete it(Y/N)?")
			choice=raw_input()
			if choice=="Y":
				conn.delete_stack(args.dele[0])
                		print("Deleting the stack:"+args.dele[0])
				return
			if choice=="N":
				print('\nAbroting the delete operation!')
			else:
				print("\nEnter a valid entry! (Y/N)?")
				delstack(j)
def testelb():
        client = boto3.client('elb')
        s=(client.describe_load_balancers())
        list=s.get('LoadBalancerDescriptions')
        f=[]
        x=0
        for i in (0,len(list)-1):
                start ="DNSName': '"
                end = "', u'SecurityGroups'"
                s1=str(list[i])
                s2=s1.split(start)[1].split(end)[0]
#               print s2
                s2="http://"+s2
                status=str(requests.get(s2))
                if status=="<Response [200]>":
                        print"\nELB is fine!!"
                        print"ELB:"+s2
                        print "Status code is:"+status+"\n"
                        print "***********************************************************************************************"
                else:
                        print"\nELB:"+s2
                        print "NO! Something wrong with ELB"
                        print "Status code is:"+status+"\n"
                        print "***********************************************************************************************"
                        f.append(s2)
                        x=1
        if x!=0:
                print "***********************************List of failed ELB(s)***************************************"
                for i in f:
                        print i
def testelbhealth(j):
	try:
		client = boto3.client('elb')
		response = client.describe_load_balancers()
		for i in range(0,len(response['LoadBalancerDescriptions'])):
			elb_name=response['LoadBalancerDescriptions'][i]['LoadBalancerName']
			elb_dns=response['LoadBalancerDescriptions'][i]['DNSName']
			elb_port=response['LoadBalancerDescriptions'][i]['ListenerDescriptions'][0]['Listener']['LoadBalancerPort']
                        elb_scheme=response['LoadBalancerDescriptions'][i]['Scheme']

			response_health = client.describe_instance_health(LoadBalancerName=elb_name)
			print('\n|-------------------------------------------------------------------------------------------------------------------------------------------|')
			print('|'+'\t'+'Load Balancer Port:'+str(elb_port).ljust(40)+'                                                                         |')
			print('|\tLoad Balancer Scheme:'+str(elb_scheme).ljust(40)+'                                                                       |')
			print('|\tLoad Balancer Name:'+str(elb_name).ljust(40)+'                                                                         |')
			print('|'+'\t'+'Load Balancer DNS Name:'+str(elb_dns).ljust(40)+'                                       |')
			print('|-------------------------------------------------------------------------------------------------------------------------------------------|')
			print('|'+'\t'+'   Instance Id                    State                                                                                             |')
			print('|-------------------------------------------------------------------------------------------------------------------------------------------|')
			for j in range(0,len(response_health['InstanceStates'])):
				id=(response_health['InstanceStates'][j]['InstanceId'])
				s=(response_health['InstanceStates'][j]['State'])
				print('|'+'\t'+'{}'.format(id).ljust(30) +'{}'.format(s).ljust(32)+'                                                                      |')
			print('|-------------------------------------------------------------------------------------------------------------------------------------------|\n')
	except Exception as e:
		print("\nOOPS! An error occured while processing the request!")
		print (str(e)+"\n")

def copy():
        try:
		source_file='CF_Template.json'
		dest_bucket='cf-template-krishna'
		dest_file='CF_Template.json'
		if raw_input('Starting copy of the file {} to the S3 bucket {}. Do you wanto change any parameters?'.format(source_file,dest_bucket)).lower()=='n':
			s3.meta.client.upload_file(source_file, dest_bucket,dest_file)
        	        print('File copied!')
		else:
			source_file=raw_input('Enter the source file name[CF_Template.json]:') or 'CF_Template.json'
			dest_file=source_file
			dest_bucket=raw_input('\nEnter the destination S3 bucket name[cf-template-krishna]:') or 'cf-template-krishna'
			s3.meta.client.upload_file(source_file, dest_bucket,dest_file)
                        print('File copied!')
        except Exception as e:
                print("\nOOPS! An error occured while processing the request!")
                print(str(e)+'\n')
def main():
	if not  test_iam_creds():
		print('IAM creds are not valid. Exiting!')
		sys.exit(-2)
	if args.add:
	        createstack(args.add[0])

	if args.list:
        	liststack(args.list[0])
	if args.dele:
        	str1 = "Stack with id "+str(args.dele[0])+" does not exist"
        	j= ""
        	try:
                	conn.describe_stacks(stack_name_or_id=args.dele[0])
        	except Exception as e:
                    	j=e.error_message
        	if j==str1:
                	    print ("\nThere is no stack named:"+args.dele[0]+" to delete!!!\n")
        	else:
                	delstack(args.dele[0])
	if args.test:
        	testelb()
	if args.parse:
        	parse()
	if args.update:
        	updatestack(args.update[0])
        if args.elb:
                testelbhealth(args.elb[0])
	if args.copy:
		copy()
		test_iam_creds()
if __name__ == "__main__":
	main()
