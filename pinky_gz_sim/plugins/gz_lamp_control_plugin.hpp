#ifndef SYSTEM_PLUGIN_GZ_LAMP_CONTROL_HH_
#define SYSTEM_PLUGIN_GZ_LAMP_CONTROL_HH_

#include <mutex>
#include <string>

#include <gz/sim/System.hh>
#include <gz/sim/Model.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/color.pb.h>

namespace pinky_gz_sim
{
    class LampControlPlugin:
        public gz::sim::System,
        public gz::sim::ISystemConfigure,
        public gz::sim::ISystemPreUpdate
    {
        public: void Configure(const gz::sim::Entity &_entity,
            const std::shared_ptr<const sdf::Element> &_sdf,
            gz::sim::EntityComponentManager &_ecm,
            gz::sim::EventManager &_eventMgr) override;

        public: void PreUpdate(const gz::sim::UpdateInfo &_info,
            gz::sim::EntityComponentManager &_ecm) override;

        private: void OnColor(const gz::msgs::Color &_msg);

        private:
            gz::sim::Model model_;
            gz::transport::Node node_;
            gz::transport::Node::Publisher material_pub_;

            std::mutex color_mutex_;
            gz::msgs::Color color_;

            std::string lamp_visual_;
            double last_update_time_{0.0};
    };
}

#endif //SYSTEM_PLUGIN_GZ_LAMP_CONTROL_HH_
