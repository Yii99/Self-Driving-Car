#include <uWS/uWS.h>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include "Eigen-3.3/Eigen/Core"
#include "Eigen-3.3/Eigen/QR"
#include "helpers.h"
#include "json.hpp"
#include "spline.h"

// for convenience
using nlohmann::json;
using std::string;
using std::vector;

int main() {
  uWS::Hub h;

  // Load up map values for waypoint's x,y,s and d normalized normal vectors
  vector<double> map_waypoints_x;
  vector<double> map_waypoints_y;
  vector<double> map_waypoints_s;
  vector<double> map_waypoints_dx;
  vector<double> map_waypoints_dy;

  // Waypoint map to read from
  string map_file_ = "../data/highway_map.csv";
  // The max s value before wrapping around the track back to 0
  double max_s = 6945.554;

  std::ifstream in_map_(map_file_.c_str(), std::ifstream::in);
  // File open for reading
  string line;
  // getline() used to read a string or a line from an input stream
  while (getline(in_map_, line)) {
    // line = [[x,y,s,d_x,d_y],...,[x,y,s,d_x,d_y]]
    std::istringstream iss(line);
    double x;
    double y;
    float s;
    float d_x;
    float d_y;
    iss >> x;
    iss >> y;
    iss >> s;
    iss >> d_x;
    iss >> d_y;
    map_waypoints_x.push_back(x);
    map_waypoints_y.push_back(y);
    map_waypoints_s.push_back(s);
    map_waypoints_dx.push_back(d_x);
    map_waypoints_dy.push_back(d_y);
  }
  
  int lane = 1;
  double curr_vel = 0.0;
  
  h.onMessage([&map_waypoints_x,&map_waypoints_y,&map_waypoints_s,
               &map_waypoints_dx,&map_waypoints_dy,&curr_vel,&lane]
              (uWS::WebSocket<uWS::SERVER> ws, char *data, size_t length,
               uWS::OpCode opCode) {
    // "42" at the start of the message means there's a websocket message event.
    // The 4 signifies a websocket message
    // The 2 signifies a websocket event
    if (length && length > 2 && data[0] == '4' && data[1] == '2') {

      auto s = hasData(data);

      if (s != "") {
        auto j = json::parse(s);
        
        string event = j[0].get<string>();
        
        if (event == "telemetry") {
          // j[1] is the data JSON object
          
          // Main car's localization Data
          double car_x = j[1]["x"];
          double car_y = j[1]["y"];
          double car_s = j[1]["s"];
          double car_d = j[1]["d"];
          double car_yaw = j[1]["yaw"];
          double car_speed = j[1]["speed"];

          // Previous path data given to the Planner
          auto previous_path_x = j[1]["previous_path_x"];
          auto previous_path_y = j[1]["previous_path_y"];
          // Previous path's end s and d values 
          double end_path_s = j[1]["end_path_s"];
          double end_path_d = j[1]["end_path_d"];

          // Sensor Fusion Data, a list of all other cars on the same side 
          //   of the road.
          auto sensor_fusion = j[1]["sensor_fusion"];

          json msgJson;

          vector<double> next_x_vals;
          vector<double> next_y_vals;

          /**
           *   define a path made up of (x,y) points that the car will visit
           *   sequentially every .02 seconds
           */
          
          // The previous points returned by the simulator can be used to guide             
          // the car to follow the previous path and to assist the calculation of
          // new trajectory points.
          int prev_size = previous_path_x.size();
          
          // Collision detection
          // if the previous points exist, set car_s to be the previous last point 
          // Frenet coordinates make the calculation easier. 
          // s is the segments along the road, d is the car position side-to-side
          if (prev_size > 0){
             car_s = end_path_s;
          }

          // Set to true if our car is getting too close to another
          bool is_too_close = false;
          // Set to true if another lane is available to be moved in
          bool is_left_lane_available = true;
          bool is_right_lane_available = true;
          bool switch_lane = false;
          int car_lane;

          
          // Loop through each sensor data
          for (int i=0; i<sensor_fusion.size(); ++i){
              float d = sensor_fusion[i][6];
              // Check if any car is in the same lane of our car
              // Assume there are 3 lanes, left, right and our lane
              // lane width = 4, if d<4, the car is in the left lane
              // if 4<d<=8, the car is in the middle lane, otherwise, it's in the right lane
              if (d <= 4){
                 car_lane = 0;
              }
              else if (d > 4 && d <= 8){
                 car_lane = 1;
              }
              else if (d > 8 && d <=12){
                 car_lane = 2; 
              }
            
              // Save the car's measurements
              double other_car_vx = sensor_fusion[i][3];
              double other_car_vy = sensor_fusion[i][4];
              double other_car_s_position = sensor_fusion[i][5];
              double other_car_speed = sqrt(other_car_vx * other_car_vx + other_car_vy * other_car_vy);
            
              // Project this car's position in the future
              // timestep used by simulator is 0.02
              other_car_s_position += ((double) prev_size * 0.02 * other_car_speed);
            
              // Check if the other car is in front of our car within a certain range (30m)
              bool within_certain_gap = abs(other_car_s_position - car_s) < 30;
            
              if (car_lane == lane && (other_car_s_position > car_s) && within_certain_gap){
                 // Set a flag if our car being too close to another one in the same lane
                 is_too_close = true;
                 // Set a flag to prepare to switch lanes
                 switch_lane = true;
              }
              else if (car_lane == (lane-1) && within_certain_gap){
                 // The other car is in the left lane
                 is_left_lane_available = false;
              }
              else if (car_lane == (lane+1) && within_certain_gap){
                 // The other car is in the right lane
                 is_right_lane_available = false;
              }   
          }
          
          // If our car is too close to another car, slow down the speed. Otherwise, speed up          
          if (is_too_close){
             curr_vel -= 0.224;
          }
          else if (curr_vel < 49.5){
             curr_vel += 0.224;
          }
          
          // Switch lanes if available
          if (switch_lane){
             if (is_left_lane_available && lane > 0){
                lane -= 1;
             }
             else if (is_right_lane_available && lane < 2){
                lane += 1;
             }
          }
          
          // Create a list of widely spaced waypoints which will be interpolated with a spline
          vector<double> list_xpts, list_ypts;
          
          // Get a reference for the car's starting point
          double ref_x = car_x;
          double ref_y = car_y;
          double ref_yaw = deg2rad(car_yaw);
          
          // If the previous path has less than 2 points, we can use the current state to generate two points
          if (prev_size < 2 ){
             double prev_car_x = ref_x - cos(ref_yaw);
             double prev_car_y = ref_y - sin(ref_yaw);
          
              // Add the previous points and current state to the list
              list_xpts.push_back(prev_car_x);
              list_xpts.push_back(ref_x);
              list_ypts.push_back(prev_car_y);
              list_ypts.push_back(ref_y);
          }
          else {
          // If there are more previous points, redefine the current state by using the endpoint and the second last point
             ref_x = previous_path_x[prev_size - 1];
             ref_y = previous_path_y[prev_size - 1];
            
             double prev_ref_x = previous_path_x[prev_size - 2];
             double prev_ref_y = previous_path_y[prev_size - 2];
            
             ref_yaw = atan2(ref_y - prev_ref_y, ref_x - prev_ref_x);
             
             list_xpts.push_back(prev_ref_x);
             list_xpts.push_back(ref_x);
             list_ypts.push_back(prev_ref_y);
             list_ypts.push_back(ref_y);     
          }
          

          vector<double> next_wp0 = getXY(car_s+30, (2+4*lane), map_waypoints_s, map_waypoints_x, map_waypoints_y);
          vector<double> next_wp1 = getXY(car_s+60, (2+4*lane), map_waypoints_s, map_waypoints_x, map_waypoints_y);
          vector<double> next_wp2 = getXY(car_s+90, (2+4*lane), map_waypoints_s, map_waypoints_x, map_waypoints_y);
          list_xpts.push_back(next_wp0[0]);
          list_xpts.push_back(next_wp1[0]);
          list_xpts.push_back(next_wp2[0]);
          list_ypts.push_back(next_wp0[1]);
          list_ypts.push_back(next_wp1[1]);
          list_ypts.push_back(next_wp2[1]);
          
          // Transform the waypoints to the local car coordinates
          for (int i=0; i<list_xpts.size(); ++i){
              double shift_x = list_xpts[i] - ref_x;
              double shift_y = list_ypts[i] - ref_y;
            
              list_xpts[i] = shift_x * cos(0 - ref_yaw) - shift_y * sin(0 - ref_yaw);
              list_ypts[i] = shift_x * sin(0 - ref_yaw) + shift_y * cos(0 - ref_yaw);
          }
          
          // Create a spline
          tk::spline s;
          s.set_points(list_xpts, list_ypts);
          
          //Fill up the next path points with leftover previous path points
          for (int i=0; i<prev_size; ++i){
              next_x_vals.push_back(previous_path_x[i]);
              next_y_vals.push_back(previous_path_y[i]);
          }
          
          // Calculate the number of break points in spline
          double target_x = 30.0;
          double target_y = s(target_x);
          double target_distance = sqrt(target_x*target_x + target_y*target_y);
          
          double x_add_on = 0;
          
          for (int i=1; i<=50-previous_path_x.size(); ++i){
               double N = target_distance/(0.02 * curr_vel /2.24);
               // Generate x and y spline points
               double x_point = x_add_on + target_x/N;
               double y_point = s(x_point);
               x_add_on = x_point;
               // Transform back to global frame
               double x_ref = x_point;
               double y_ref = y_point;
            
               // Rotate from the car's coordinate system to the map coordinate system
               x_point = x_ref * cos(ref_yaw) - y_ref * sin(ref_yaw);
               y_point = x_ref * sin(ref_yaw) + y_ref * cos(ref_yaw);
            
               x_point += ref_x;
               y_point += ref_y;
            
               next_x_vals.push_back(x_point);
               next_y_vals.push_back(y_point);
          }
          
          msgJson["next_x"] = next_x_vals;
          msgJson["next_y"] = next_y_vals;

          auto msg = "42[\"control\","+ msgJson.dump()+"]";

          ws.send(msg.data(), msg.length(), uWS::OpCode::TEXT);
        }  // end "telemetry" if
      } else {
        // Manual driving
        std::string msg = "42[\"manual\",{}]";
        ws.send(msg.data(), msg.length(), uWS::OpCode::TEXT);
      }
    }  // end websocket if
  }); // end h.onMessage

  h.onConnection([&h](uWS::WebSocket<uWS::SERVER> ws, uWS::HttpRequest req) {
    std::cout << "Connected!!!" << std::endl;
  });

  h.onDisconnection([&h](uWS::WebSocket<uWS::SERVER> ws, int code,
                         char *message, size_t length) {
    ws.close();
    std::cout << "Disconnected" << std::endl;
  });

  int port = 4567;
  if (h.listen(port)) {
    std::cout << "Listening to port " << port << std::endl;
  } else {
    std::cerr << "Failed to listen to port" << std::endl;
    return -1;
  }
  
  h.run();
}
