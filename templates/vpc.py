from troposphere import Template, Ref, Output, Export, Sub
from troposphere.ec2 import (
  VPC,
  InternetGateway,
  VPCGatewayAttachment,
  Subnet,
  Route,
  RouteTable,
  SubnetRouteTableAssociation
)

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
    # Public resources vars
    self.public_subnets = sceptre_user_data['resources']['vpc']['public']['subnets']
    self.public_route_table_name = sceptre_user_data['resources']['vpc']['public']['route_table_name']

    # Create stack resources
    self.create_vpc()
    self.create_igw()
    self.create_public_resources()
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

  # Create Route Table resource
  def create_route_table(self, route_table_name, vpc_name):
    t = self.template
    t.add_resource(
      RouteTable(
        route_table_name,
        VpcId=Ref(vpc_name)
      )
    )

  # Create Subnet -> Route Table association resource
  def create_subnet_route_association(self, subnet_name, route_table_name):
    association_name = subnet_name + "RouteAssociation"
    t = self.template
    t.add_resource(
      SubnetRouteTableAssociation(
        association_name,
        SubnetId=Ref(subnet_name),
        RouteTableId=Ref(route_table_name)
      )
    )

  # Create Route resource
  def create_route(self, route_name, route_dependency, gateway_name, destination_cidr_block, route_table_name):
    t = self.template
    t.add_resource(
      Route(
        route_name,
        DependsOn=route_dependency,
        GatewayId=Ref(gateway_name),
        DestinationCidrBlock=destination_cidr_block,
        RouteTableId=Ref(route_table_name)
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

  # Define CloudFormation public network(s) resource(s)
  def create_public_resources(self):
    igw_attachment = self.igw_attachment
    igw_name = self.igw_name
    public_route_table_name = self.public_route_table_name
    vpc_name = self.vpc_name
    self.create_route_table(public_route_table_name, vpc_name)
    self.create_route("PublicInternetRoute", igw_attachment, igw_name, "0.0.0.0/0", public_route_table_name)

  # Define CloudFormation Subnet resources
  def create_subnets(self):
    public_subnets = self.public_subnets
    for list_item in range(len(public_subnets)):
      name = public_subnets[list_item]["name"]
      cidr = public_subnets[list_item]["cidr"]
      vpc_name = self.vpc_name
      az = public_subnets[list_item]["az"]
      self.create_subnet(name, cidr, vpc_name, az)
      self.create_subnet_route_association(name, self.public_route_table_name)

# Return CloudFormation stack as a string
def sceptre_handler(sceptre_user_data):
  stack = vpc(sceptre_user_data)
  return stack.template.to_yaml()
