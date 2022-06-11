#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/laser_scan.hpp"

class Listener : public rclcpp::Node{
	public:
		Listener() : Node("lidar_listener"){
			subscription_ = this->create_subscription<sensor_msgs::msg::LaserScan>("scan", rclcpp::SensorDataQoS(), std::bind(&Listener::topic_callback, this, std::placeholders::_1));
		}

	private:
		void topic_callback(sensor_msgs::msg::LaserScan::SharedPtr scan) const{
			int count = scan->scan_time/scan->time_increment + 1;
			RCLCPP_INFO(this->get_logger(), "I got %d values", count);
			for(int i = 0; i < count-1; i++){
				printf("i: %.3f, ", scan->ranges[i]);
			}
			printf("\n");
		}
		rclcpp::Subscription<sensor_msgs::msg::LaserScan>::SharedPtr subscription_;

};


int main(int argc, char*argv[]){
	rclcpp::init(argc, argv);
	rclcpp::spin(std::make_shared<Listener>());
	rclcpp::shutdown();
	return 0;
}
