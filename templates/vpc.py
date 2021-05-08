from troposphere import Template, Ref, Output, Export, Sub
from troposphere.ec2 import VPC

class vpc(object):

  def __init__(self, sceptre_user_data):
    self.template = Template()
    self.template.set_version()
    # VPC vars
    self.vpc_name = "VPC"
    self.vpc_cidr = sceptre_user_data['resources']['vpc']['cidr']

    self.create_vpc()

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


# Return CloudFormation stack as a string
def sceptre_handler(sceptre_user_data):
  stack = vpc(sceptre_user_data)
  return stack.template.to_yaml()