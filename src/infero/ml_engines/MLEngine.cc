/*
 * (C) Copyright 1996- ECMWF.
 *
 * This software is licensed under the terms of the Apache Licence Version 2.0
 * which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
 * In applying this licence, ECMWF does not waive the privileges and immunities
 * granted to it by virtue of its status as an intergovernmental organisation
 * nor does it submit to any jurisdiction.
 */

#include <vector>
#include <string>

#include "eckit/exception/Exceptions.h"
#include "eckit/log/Log.h"

#include "infero/ml_engines/MLEngine.h"
#include "infero/utils.h"


#ifdef HAVE_ONNX
#include "infero/ml_engines/MLEngineONNX.h"
#endif

#ifdef HAVE_TFLITE
#include "infero/ml_engines/MLEngineTFlite.h"
#endif

#ifdef HAVE_TENSORRT
#include "infero/ml_engines/MLEngineTRT.h"
#endif

using namespace eckit;

namespace infero {


MLEngine::~MLEngine() {}

std::unique_ptr<MLEngine> MLEngine::create(std::string choice, std::string model_path) {

    trim(choice);
    trim(model_path);

    Log::info() << "Loading model " << model_path << std::endl;

#ifdef HAVE_ONNX
    if (choice.compare("onnx") == 0) {

        Log::info() << "creating RTEngineONNX.. " << std::endl;

        return std::unique_ptr<MLEngine>(new MLEngineONNX(model_path));
    }
#endif

#ifdef HAVE_TFLITE
    if (choice.compare("tflite") == 0) {

        Log::info() << "creating RTEngineTFlite.. " << std::endl;

        return std::unique_ptr<MLEngine>(new MLEngineTFlite(model_path));
    }
#endif

#ifdef HAVE_TENSORRT
    if (choice.compare("tensorrt") == 0) {

        Log::info() << "creating MLEngineTRT.. " << std::endl;

        return std::unique_ptr<MLEngine>(new MLEngineTRT(model_path));
    }
#endif

    throw BadValue("Engine type " + choice + " not supported!", Here());
}


int MLEngine::create_handle(string choice, string model_path) {

    // append this instance to the map_
    if (map_.find(gid_) != map_.end())
        throw SeriousBug("Handle " + std::to_string(gid_) + " already opened!", Here());

    // add the handle to map_
    map_[gid_] = create(choice, model_path);

    Log::info() << "Created ML Engine handle: "
                << gid_ << std::endl;

    // increment the global handle count
    return gid_++;
}

void MLEngine::close_handle(int handle_id)
{

    if (map_.find(handle_id) == map_.end())
        throw OutOfRange("Handle " + std::to_string(handle_id) + " not opened!", Here());

    // remove the handle from map_
    map_.erase(handle_id);

    Log::info() << "Closed ML Engine handle: "
                << handle_id << std::endl;
}

std::unique_ptr<MLEngine> &MLEngine::get_model(int handle_id){

    if (map_.find(handle_id) == map_.end())
        throw OutOfRange("Handle " + std::to_string(handle_id) + " not opened!", Here());

    return map_[handle_id];
}


int MLEngine::gid_ = 0;

std::map<int, std::unique_ptr<MLEngine>> MLEngine::map_;


}  // namespace infero
