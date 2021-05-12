from troposphere import (
  Template,
  Ref,
  Output,
  Export,
  Sub,
  GetAtt
)
from troposphere.ec2 import (
  VPC,
  InternetGateway,
  VPCGatewayAttachment,
  Subnet,
  Route,
  RouteTable,
  SubnetRouteTableAssociation,
  EIP,
  NatGateway
)

class vpc(object):

  def __init__(self, sceptre_user_data):
    self.template = Template()
    self.template.set_version()
    self.sceptre_user_data = sceptre_user_data
    # VPC vars
    self.vpc_name = "VPC"
    self.vpc_cidr = sceptre_user_data['resources']['vpc']['cidr']
    # Internet Gateway vars
    self.igw_name = "InternetGateway"
    self.igw_attachment = str(self.igw_name + "Attachment")
    # Public resources vars
    self.public_subnets = sceptre_user_data['resources']['vpc']['public']['subnets']
    self.public_route_table_name = "PublicRouteTable"
    # Private resources vars
    self.private_subnets = sceptre_user_data['resources']['vpc']['private']['subnets']

    # Create stack resources
    self.create_vpc()
    self.create_igw()
    self.create_public_resources()
    self.create_private_resources()
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
  def create_route(self, route_dict):
    t = self.template
    t.add_resource(Route(**route_dict))

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
    public_route_table_name = "PublicRouteTable"
    vpc_name = self.vpc_name
    self.create_route_table(self.public_route_table_name, vpc_name)
    route_dict = {
      "title": "PublicInternetRoute",
      "DependsOn": igw_attachment,
      "GatewayId": Ref(self.igw_name),
      "DestinationCidrBlock": "0.0.0.0/0",
      "RouteTableId": Ref(self.public_route_table_name)
    }
    self.create_route(route_dict)

  # Define CloudFormation private network(s) resource(s)
  def create_private_resources(self):
    # If only a single NAT gateway name is defined, then this implies that the environment may have
    # multiple private subnets that will be attached with that single NAT gateway via a single private
    # route table.
    vpc_name = self.vpc_name
    t = self.template
    if "single_nat_gateway" in self.sceptre_user_data['resources']['vpc']['private']:
      if self.sceptre_user_data['resources']['vpc']['private']['single_nat_gateway'] is True:
        nat_gateway_name = "PrivateNATGateway"
        nat_gateway_subnet = self.public_subnets[0]["name"]
        nat_gateway_eip = nat_gateway_name + "EIP"
        nat_gateway_route_name = nat_gateway_name + "Route"
        private_route_table_name = "PrivateNetRouteTable"
        self.create_route_table(private_route_table_name, vpc_name)
        t.add_resource(
          EIP(
            nat_gateway_eip,
            Domain="vpc"
          )
        )
        t.add_resource(
          NatGateway(
            nat_gateway_name,
            AllocationId=GetAtt(nat_gateway_eip, 'AllocationId'),
            SubnetId=Ref(nat_gateway_subnet)
          )
        )
        route_dict = {
          "title": "PrivateRouteTable",
          "NatGatewayId": Ref(nat_gateway_name),
          "DestinationCidrBlock": "0.0.0.0/0",
          "RouteTableId": Ref(private_route_table_name),
        }
        self.create_route(route_dict)


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
