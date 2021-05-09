from troposphere import Template, Ref, Output, Export, Sub
from troposphere.ec2 import VPC, InternetGateway, VPCGatewayAttachment, Subnet

class vpc(object):

  def __init__(self, sceptre_user_data):
    self.template = Template()
    self.template.set_version()
    # VPC vars
    self.vpc_name = "VPC"
    self.vpc_cidr = sceptre_user_data['resources']['vpc']['cidr']
    # Internet Gateway vars
    self.igw_name = "InternetGateway"
    self.igw_attachment = str(self.igw_name + "Attachment")
    # Public Subnet vars
    self.public_subnets = sceptre_user_data['resources']['vpc']['subnets']['public']

    # Create stack resources
    self.create_vpc()
    self.create_igw()
    self.create_subnets()

  ## Generic VPC functions
  # Create VPC Subnet resource
  def create_subnet(self, subnet_name, cidr_block, vpc_name, availability_zone):
    t = self.template
    t.add_resource(
      Subnet(
        subnet_name,
        CidrBlock=cidr_block,
        VpcId=Ref(vpc_name),
        AvailabilityZone=availability_zone
      )
    )

  # Define CloudFormation VPC resource
  def create_vpc(self):
    t = self.template
    t.add_resource(
      VPC(
        self.vpc_name,
        CidrBlock=self.vpc_cidr,
        EnableDnsHostnames=True,
        EnableDnsSupport=True
      )
    )
    t.add_output(
      Output(
        "VPCID",
        Value=Ref(self.vpc_name),
        Export=Export(
          Sub("${AWS::StackName}-" + self.vpc_name + "-ID")
        )
      )
    )

  # Define CloudFormation Internet Gateway resources
  def create_igw(self):
    t = self.template
    t.add_resource(
      InternetGateway(
        self.igw_name
      )
    )
    t.add_resource(
      VPCGatewayAttachment(
        self.igw_attachment,
        VpcId=Ref(self.vpc_name),
        InternetGatewayId=Ref(self.igw_name)
      )
    )

  # Define CloudFormation Subnet resources
  def create_subnets(self):
    public_subnets = self.public_subnets
    for list_item in range(len(public_subnets)):
      name = public_subnets[list_item]["name"]
      cidr = public_subnets[list_item]["cidr"]
      vpc_name = self.vpc_name
      az = public_subnets[list_item]["az"]
      self.create_subnet(name, cidr, vpc_name, az)

# Return CloudFormation stack as a string
def sceptre_handler(sceptre_user_data):
  stack = vpc(sceptre_user_data)
  return stack.template.to_yaml()
