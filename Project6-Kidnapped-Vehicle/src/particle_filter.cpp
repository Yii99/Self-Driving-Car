#include "particle_filter.h"

#include <math.h> 
#include <algorithm> 
#include <iostream> 
#include <iterator> 
#include <numeric> 
#include <random> 
#include <string> 
#include <vector> 
#include <sstream>

#include "helper_functions.h"

using std::string;
using std::vector;

static std::default_random_engine gen;

void ParticleFilter::init(double x, double y, double theta, double std[]) {
/**
* Initialize all particles to first position 
* (based on estimates of x, y, theta and their uncertainties from GPS) and all weights to 1. 
*/
  
  // Set the number of particles
  num_particles = 100;  // Set the number of particles
  
  // Creates normal (Gaussian) distribution
  std::normal_distribution<double> dist_x(x, std[0]);
  std::normal_distribution<double> dist_y(y, std[1]);
  std::normal_distribution<double> dist_theta(theta, std[2]);
  
  // Instantiate a new particle
  for (int i=0; i<num_particles; ++i){
       Particle p;
       p.id = i;
       p.x = dist_x(gen);
       p.y = dist_y(gen);
       p.theta = dist_theta(gen);
       p.weight = 1.0;
    
       // Add the particle to the particle filter set
       particles.push_back(p);
  }
  is_initialized = true; 
}



void ParticleFilter::prediction(double delta_t, double std_pos[], 
                                double velocity, double yaw_rate) {
/**
* Add measurements to each particle and add random Gaussian noise
*/
  
  // Normal distribution for sensor noise
  std::normal_distribution<double> dist_x(0, std_pos[0]);
  std::normal_distribution<double> dist_y(0, std_pos[1]);
  std::normal_distribution<double> dist_theta(0, std_pos[2]);
  
  for (int i=0; i<num_particles; ++i){
       if (fabs(yaw_rate)<0.00001){
           particles[i].x += velocity * delta_t * cos(particles[i].theta);
           particles[i].y += velocity * delta_t * sin(particles[i].theta);
       }
       else{
           particles[i].x += velocity / yaw_rate * (sin(particles[i].theta + yaw_rate * delta_t) - sin(particles[i].theta));
           particles[i].y += velocity / yaw_rate * (cos(particles[i].theta) - cos(particles[i].theta + yaw_rate * delta_t));
           particles[i].theta += yaw_rate * delta_t;
       }
    
       // Update particle with noise
       particles[i].x += dist_x(gen);
       particles[i].y += dist_y(gen);
       particles[i].theta += dist_theta(gen);
  }
}


void ParticleFilter::dataAssociation(vector<LandmarkObs> predicted, 
                                     vector<LandmarkObs>& observations) {
/**
* Find the predicted measurement that is closest to each observed measurement and assign the observed measurement to this particular landmark
*/

   // Loop each observed measurement
   for (unsigned int i=0; i<observations.size(); ++i){
        double min_dist = std::numeric_limits<double>::max();
        int map_id;

        // Loop each predicted measurement
        for (unsigned int j=0; j<predicted.size(); ++j){
             double d_x = observations[i].x - predicted[j].x;
             double d_y = observations[i].y - predicted[j].y;
             double d = d_x * d_x + d_y * d_y;
             if (d < min_dist){
                 min_dist = d;
                 map_id = predicted[j].id;
             }   
        }
        observations[i].id = map_id; 

   }

}

void ParticleFilter::updateWeights(double sensor_range, double std_landmark[], 
                                   const std::vector<LandmarkObs> &observations, 
                                   const Map &map_landmarks) {
/**
* Update the weights of each particle using a mult-variate Gaussian distribution
*/
  
// Loop each particle
   for (int i=0; i<num_particles; ++i){
        // gather current values
        double p_x = particles[i].x;
        double p_y = particles[i].y;
        double p_theta = particles[i].theta;
     
        // List all landmarks within sensor range
        vector<LandmarkObs> predictions;
     
        // Each map landmark for loop
        for (unsigned int j=0; j<map_landmarks.landmark_list.size(); ++j){
             int l_id = map_landmarks.landmark_list[j].id_i;
             float l_x = map_landmarks.landmark_list[j].x_f;
             float l_y = map_landmarks.landmark_list[j].y_f;
            
             // Only consider landmarks within sensor range of the particle
             if (fabs(l_x-p_x) <= sensor_range && fabs(l_y-p_y) <= sensor_range){
                 predictions.push_back(LandmarkObs{l_id, l_x, l_y});
             }
        }
     
        // List all observations in map coordinates
        vector<LandmarkObs> transformed_obs;
        for (unsigned int j=0; j<observations.size(); ++j){
             double t_x = cos(p_theta)*observations[j].x - sin(p_theta)*observations[j].y + p_x;
             double t_y = sin(p_theta)*observations[j].x + cos(p_theta)*observations[j].y + p_y;
             transformed_obs.push_back(LandmarkObs{observations[j].id, t_x, t_y});
        }
     
        // Data association for the predictions and transformed observations on current particle
        dataAssociation(predictions, transformed_obs);
     
        // Compute the likelihood for each particle,
        // which is the probablity of obtaining current observations being in state (particle_x, particle_y, particle_theta)
     
        particles[i].weight = 1.0;
     
        for (unsigned int j=0; j<transformed_obs.size(); ++j){
             double obs_x, obs_y, mu_x, mu_y;
             obs_x = transformed_obs[j].x;
             obs_y = transformed_obs[j].y;
          
             for (unsigned int k=0; k<predictions.size(); ++k){
                  if (predictions[k].id == transformed_obs[j].id){
                      mu_x = predictions[k].x;
                      mu_y = predictions[k].y;
                      break;
                  }
             }
          
             double std_x = std_landmark[0];
             double std_y = std_landmark[1];
             double prob = (1/(2*M_PI*std_x*std_y))*exp(-(pow(obs_x-mu_x,2)/(2*pow(std_x,2))+(pow(obs_y-mu_y,2)/(2*pow(std_y,2)))));
          
             particles[i].weight *= prob;
          
        }
   }
}

void ParticleFilter::resample() {
/**
* Resample particles with replacement with probability proportional to their weight. 
*/

   //
   vector<double> weights;
   double mw = std::numeric_limits<double>::min();
   for (int i=0; i<num_particles; ++i){
        weights.push_back(particles[i].weight);
        if (particles[i].weight > mw){
            mw = particles[i].weight;
        }
   }
  
   
   std::discrete_distribution<> dist_weights(weights.begin(),weights.end());
   std::uniform_int_distribution<int> dist_index(0, num_particles-1);
   vector<Particle> resampled_particles;
   
   double beta = 0.0;
   int index = dist_index(gen);
   for (int i=0; i<num_particles; ++i){
        beta += dist_weights(gen) * 2.0 * mw;
        while (weights[index]<beta){
               beta -= weights[index];
               index = (index + 1) % num_particles;
        }
        resampled_particles.push_back(particles[index]);
   }
   particles = resampled_particles;
}

void ParticleFilter::SetAssociations(Particle& particle, 
                                     const vector<int>& associations, 
                                     const vector<double>& sense_x, 
                                     const vector<double>& sense_y) {
  // particle: the particle to which assign each listed association, 
  //   and association's (x,y) world coordinates mapping
  // associations: The landmark id that goes along with each listed association
  // sense_x: the associations x mapping already converted to world coordinates
  // sense_y: the associations y mapping already converted to world coordinates
  particle.associations= associations;
  particle.sense_x = sense_x;
  particle.sense_y = sense_y;
}

string ParticleFilter::getAssociations(Particle best) {
  vector<int> v = best.associations;
  std::stringstream ss;
  copy(v.begin(), v.end(), std::ostream_iterator<int>(ss, " "));
  string s = ss.str();
  s = s.substr(0, s.length()-1);  // get rid of the trailing space
  return s;
}

string ParticleFilter::getSenseCoord(Particle best, string coord) {
  vector<double> v;

  if (coord == "X") {
    v = best.sense_x;
  } else {
    v = best.sense_y;
  }

  std::stringstream ss;
  copy(v.begin(), v.end(), std::ostream_iterator<float>(ss, " "));
  string s = ss.str();
  s = s.substr(0, s.length()-1);  // get rid of the trailing space
  return s;
}