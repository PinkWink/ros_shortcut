#include <string>
#include <gz/common/Console.hh>
#include <gz/plugin/Register.hh>
#include <gz/msgs/material_color.pb.h>
#include <gz/sim/Util.hh>
#include <gz/sim/World.hh>
#include <gz/sim/components/Name.hh>

#include "gz_lamp_control_plugin.hpp"

namespace pinky_gz_sim
{

void LampControlPlugin::Configure(const gz::sim::Entity &_entity,
    const std::shared_ptr<const sdf::Element> &_sdf,
    gz::sim::EntityComponentManager &_ecm,
    gz::sim::EventManager & /*_eventMgr*/)
{
    model_ = gz::sim::Model(_entity);
    auto sdfPtr = const_cast<sdf::Element *>(_sdf.get());

    lamp_visual_ = "robot_lamp_visual";
    if (sdfPtr->HasElement("link")) {
        lamp_visual_ = sdfPtr->Get<std::string>("link") + "_visual";
    }

    std::string color_topic = "lamp/color";
    if (sdfPtr->HasElement("color_topic")) {
        color_topic = sdfPtr->Get<std::string>("color_topic");
    }

    // lamp starts switched off
    color_.set_r(0.0f);
    color_.set_g(0.0f);
    color_.set_b(0.0f);
    color_.set_a(1.0f);

    const gz::sim::World world(gz::sim::worldEntity(_ecm));
    const std::string world_name = world.Name(_ecm).value_or("default");
    material_pub_ = node_.Advertise<gz::msgs::MaterialColor>(
        "/world/" + world_name + "/material_color");

    node_.Subscribe(color_topic, &LampControlPlugin::OnColor, this);

    gzmsg << "LampControlPlugin: visual [" << lamp_visual_
          << "] listening on [" << color_topic << "]" << std::endl;
}

void LampControlPlugin::OnColor(const gz::msgs::Color &_msg)
{
    std::lock_guard<std::mutex> lock(color_mutex_);
    color_ = _msg;
}

void LampControlPlugin::PreUpdate(const gz::sim::UpdateInfo &_info,
    gz::sim::EntityComponentManager & /*_ecm*/)
{
    const double current_time = std::chrono::duration<double>(_info.simTime).count();
    if (current_time - last_update_time_ < 0.05) {
        return;
    }
    last_update_time_ = current_time;

    gz::msgs::Color color;
    {
        std::lock_guard<std::mutex> lock(color_mutex_);
        color = color_;
    }

    gz::msgs::MaterialColor msg;
    msg.mutable_entity()->set_name(lamp_visual_);
    msg.set_entity_match(gz::msgs::MaterialColor::EntityMatch::MaterialColor_EntityMatch_FIRST);
    const gz::math::Color c(color.r(), color.g(), color.b(), 1.0f);
    gz::msgs::Set(msg.mutable_diffuse(), c);
    gz::msgs::Set(msg.mutable_ambient(), c);
    gz::msgs::Set(msg.mutable_emissive(), c);
    material_pub_.Publish(msg);
}

}

GZ_ADD_PLUGIN(
    pinky_gz_sim::LampControlPlugin,
    gz::sim::System,
    pinky_gz_sim::LampControlPlugin::ISystemConfigure,
    pinky_gz_sim::LampControlPlugin::ISystemPreUpdate)
