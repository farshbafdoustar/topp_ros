#!/usr/bin/env python

import copy, time

# Ros imports
import rospy
from topp_ros.srv import GenerateTrajectory, GenerateTrajectoryRequest
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint, \
    MultiDOFJointTrajectory, MultiDOFJointTrajectoryPoint
from geometry_msgs.msg import Transform, Twist

class RequestTrajectory():

    def __init__(self):
        # First set up service
        request_trajectory_service = rospy.ServiceProxy(
            "generate_toppra_trajectory", GenerateTrajectory)

        # This is an example for UAV and output trajectory is converted 
        # accordingly
        trajectory_pub = rospy.Publisher('multi_dof_trajectory', 
            MultiDOFJointTrajectory, queue_size=1)
        time.sleep(0.5)

        # Example of a simple square trajectory for quadcopter. All vectors
        # must be of same length
        x = [0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0]
        y = [0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0]
        z = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
        yaw = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # Another example. Same square defined through more points. This will
        # overwrite the first example
        x = [0.0, 0.5, 1.0, 1.0, 1.0, 0.5, 0.0, 0.0, 0.0]
        y = [0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 0.5, 0.0]
        z = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]
        yaw = [0, 0, 0, 0, 0, 0, 0, 0, 0]

        # Create a service request which will be filled with waypoints
        request = GenerateTrajectoryRequest()

        # Add waypoints in request
        waypoint = JointTrajectoryPoint()
        for i in range(0, len(x)):
            # Positions are defined above
            waypoint.positions = [x[i], y[i], z[i], yaw[i]]
            # Also add constraints for velocity and acceleration. These
            # constraints are added only on the first waypoint since the
            # TOPP-RA reads them only from there.
            if i==0:
                waypoint.velocities = [2, 2, 2, 1]
                waypoint.accelerations = [1.25, 1.25, 1.25, 1]

            # Append all waypoints in request
            request.waypoints.points.append(copy.deepcopy(waypoint))

        # Set up joint names. This step is not necessary
        request.waypoints.joint_names = ["x", "y", "z", "yaw"]
        # Set up sampling frequency of output trajectory.
        request.sampling_frequency = 100.0
        # Set up number of gridpoints. The more gridpoints there are, 
        # trajectory interpolation will be more accurate but slower.
        # Defaults to 100
        request.n_gridpoints = 500
        # If you want to plot Maximum Velocity Curve and accelerations you can
        # send True in this field. This is intended to be used only when you
        # have to debug something since it will block the service until plot
        # is closed.
        request.plot = False
        # Request the trajectory
        response = request_trajectory_service(request)

        # Response will have trajectory and bool variable success. If for some
        # reason the trajectory was not able to be planned or the configuration
        # was incomplete or wrong it will return False.

        print "Converting trajectory to multi dof"
        joint_trajectory = response.trajectory
        multi_dof_trajectory = self.JointTrajectory2MultiDofTrajectory(joint_trajectory)
        trajectory_pub.publish(multi_dof_trajectory)

    def JointTrajectory2MultiDofTrajectory(self, joint_trajectory):
        multi_dof_trajectory = MultiDOFJointTrajectory()

        for i in range(0, len(joint_trajectory.points)):
            temp_point = MultiDOFJointTrajectoryPoint()
            temp_transform = Transform()
            temp_transform.translation.x = joint_trajectory.points[i].positions[0]
            temp_transform.translation.y = joint_trajectory.points[i].positions[1]
            temp_transform.translation.z = joint_trajectory.points[i].positions[2]
            temp_transform.rotation.w = 1.0

            temp_vel = Twist()
            temp_vel.linear.x = joint_trajectory.points[i].velocities[0]
            temp_vel.linear.y = joint_trajectory.points[i].velocities[1]
            temp_vel.linear.z = joint_trajectory.points[i].velocities[2]

            temp_acc = Twist()
            temp_acc.linear.x = joint_trajectory.points[i].accelerations[0]
            temp_acc.linear.y = joint_trajectory.points[i].accelerations[1]
            temp_acc.linear.z = joint_trajectory.points[i].accelerations[2]

            temp_point.transforms.append(temp_transform)
            temp_point.velocities.append(temp_vel)
            temp_point.accelerations.append(temp_acc)
            temp_point.time_from_start = joint_trajectory.points[i].time_from_start

            multi_dof_trajectory.points.append(temp_point)

        return multi_dof_trajectory


if __name__ == "__main__":
    rospy.init_node("topp_trajectory_call_example")
    RequestTrajectory()