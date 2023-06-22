# KnowledgeTransfer

This sums up my learnings during my Razorpay Internship.


## Learning

- Continuous Integration / Continuous Delivery & Deployment (CI | CD)

- GitHub Actions & GitHub Marketplace

- Docker

- Kubernetes

- Amazon Web Service 

    <img src = "images/aws_mindmap.png">

     - Architecture
        - AWS Cloud
            - Region 1
                - Availability Zone 1
                - Availability Zone 2
                - Availability Zone 3
            - Region 2
                - Availability Zone 1
                - Availability Zone 2
                - Availability Zone 3
            - Region 3
                - Availability Zone 1
                - Availability Zone 2
                - Availability Zone 3

    - IAM
        > *Identity that represents a person or application that interacts with the AWS services and resources.*
        > *The user gets access to the resources on the basis of the IAM policies which is a JSON based document.*
        > *Collection of IAM users can be grouped where the policies can be inherited.*
    
    - AWS Compute
        - Instance
            - Classification and Specification
                - General Purpose
                - Compute Optimized
                - Memory Optimized
                - Accelerated Computing
                - Storage Optimized
            - Elastic Compute Cloud (EC2)
                - Amazon Machine Image (AMI)
        - Container
            - Amazon Container Service (ECS)
            - Amazon Elastic Kubernetes Service (EKS)
        - Serverless
            - AWS Fargate
            - AWS Lambda

    <img src = "images/container_vs_vm.jpeg">

    - AWS Storage
        - Block Storage
            - Instance Store (Non-persistent fast storage just like RAM)
            - Elastic Block Store (EBS)
                - SSD (NVMe used by Amazon)
                - HDD
                - Deployed at only one Availability Zone
        - File Storage
            - Elastic File System (EFS) (For Linux)
                - Shared storage between multiple Availability Zone
            - FSx (For Windows)
        - Object Storage (Object = Data + Metadata + Key)
            - Simple Storage Service (S3 Bucket)
                - Regional Service (Available in a particular region only)
                - Global Namespace (Name/Link to the resource is globally available hence must be unique for each regions)

        > *EBS = SAN (Storage Area Network) while EFS = NAS (Network Attached Storage)*

    - AWS Databases

        <img src = "images/db.png">

        - Relational Database Service (RDS) [SQL]
            - Amazon Aurora
            - Microsoft SQL
            - MariaDB
            - MySQL
        - Amazon DynamoDB [NoSQL]
            - Key-Value Database
            - Serverless in nature

    - AWS Networking
        
      <img src = "images/vpc.png">

        - Classless Inter-Domain Routing (CIDR)
        
        <img src = "images/vpc_cidr.png">  

        - Network Acknowledgement NACL (Stateless)
        - Security Group  (Stateful)

    - Monitoring, Load Balancing and Scaling

        - Amazon CloudWatch (Monitoring)
        - Elastic Load Balancing 
            - Application Load Balancer 
            - Network Load Balancer
            - Gateway Load Balancer
            - Classic Load Balancer

            > *Client requests hit an elastic load balancer as a single point of contact and then the requests are rerouted to multiple EC2 instances thereby balancing the traffic*  

    - Scaling

        - Vertical Scaling 
            > *Increase or Scale by increasing the metrics of the previous resource*
        - Horizontal Scaling
            > *Increase or Scale by increasing the number of resources keeping individual metrics of the resources constant*
        - EC2 Auto Scaling
        
    - Misc. Tools
        - Elastic Beanstalk
        - Amazon Route 53

## Book Suggestions

- Girish
    - Concrete Mathematics - Knuth, Graham
    - All of Stats - Wasserman 
    - Statistical Design - Casella 
    - Modern Age Statistical Inference - Efron, Hastie
    - Elements of Statistical Learning - Hastie, Tibshirani
    - Probabilistic ML - Kevin Murphy
    - Deep Learning - Bengio, Goodfellow
- Murali
    - Auth N Capture - Aditya Kulkarni