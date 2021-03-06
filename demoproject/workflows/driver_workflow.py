import ujson
# from flytekit.common.tasks.task import SdkTask
from flytekit.sdk.tasks import python_task, inputs, outputs
from flytekit.sdk.types import Types
from flytekit.sdk.workflow import workflow_class, Output, Input
from workflows.classifier_evaluate_workflow import evaluate_lp
from workflows.classifier_train_workflow import train_lp, DEFAULT_VALIDATION_DATA_RATIO
from workflows.data_preparation_workflow import data_prep

DEFAULT_TRAINING_CONFIG_FILE = "models/classifier/resnet50/configs/model_training_config_demo.json"
DEFAULT_EVALUATION_CONFIG_FILE = "models/classifier/resnet50/configs/model_evaluation_config_demo.json"

# compute_confusion_matrix = SdkTask.fetch(
#     project="kubecondemo2019-metrics",
#     domain="development",
#     name="demo_metrics.tasks.confusion_matrix.confusion_matrix",
#     version="66b463748f25ef71c8cd4eb3001f00eafb83efc6",
# )


@inputs(models=[Types.Blob])
@outputs(second=Types.Blob)
@python_task(cache=True, cache_version="1")
def pick_second(wf_params, models, second):
    second.set(models[1])


@workflow_class
class DriverWorkflow:
    streams_external_storage_prefix = Input(Types.String, required=True)
    streams_names = Input([Types.String], required=True)
    stream_extension = Input(Types.String, default="avi")

    streams_metadata_path = Input(Types.String, required=True)
    training_validation_config_json = Input(Types.Generic,
                                            default=ujson.loads(open(DEFAULT_TRAINING_CONFIG_FILE).read()))
    validation_data_ratio = Input(Types.Float, default=DEFAULT_VALIDATION_DATA_RATIO)
    evaluation_config_json = Input(Types.Generic,
                                   default=ujson.loads(open(DEFAULT_EVALUATION_CONFIG_FILE).read()))

    prepare = data_prep(
        streams_external_storage_prefix=streams_external_storage_prefix,
        streams_names=streams_names,
        stream_extension=stream_extension)

    train = train_lp(
        available_streams_names=prepare.outputs.streams_names_out,
        available_streams_mpblobs=prepare.outputs.selected_frames_mpblobs,
        streams_metadata_path=streams_metadata_path,
        training_validation_config_json=training_validation_config_json,
        validation_data_ratio=validation_data_ratio
    )

    pick_second = pick_second(models=train.outputs.trained_models)

    evaluate = evaluate_lp(
        available_streams_names=prepare.outputs.streams_names_out,
        available_streams_mpblobs=prepare.outputs.selected_frames_mpblobs,
        streams_metadata_path=streams_metadata_path,
        evaluation_config_json=evaluation_config_json,
        model=pick_second.outputs.second,
        validation_data_ratio=validation_data_ratio
    )

    # confusion_matrix_task = compute_confusion_matrix(
    #     y_true=evaluate.outputs.ground_truths,
    #     y_pred=evaluate.outputs.predictions,
    #     title="Confusion Matrix",
    #     normalize=True,
    #     classes=["busy", "clear"],
    # )

    ground_truths = Output(evaluate.outputs.ground_truths, sdk_type=[Types.Integer])
    predictions = Output(evaluate.outputs.predictions, sdk_type=[Types.Integer])
    # confusion_matrix_image = Output(confusion_matrix_task.outputs.visual, sdk_type=Types.Blob)


driver_workflow_lp = DriverWorkflow.create_launch_plan()
