from kubernetes import client, config
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config.load_incluster_config()


def deploy(image: str, pipeline_version: str):
    namespace = 'retrainer'
    pod_name = 'retrainer-pod'
    deployment_name = 'retrainer-deployment'

    apps_api = client.AppsV1Api()

    pod = client.V1PodSpec(
        containers=([
            client.V1Container(
                name=pod_name,
                command=['python3'],
                args=['-m', 'inference.retrainer',
                    '--pipeline_version', pipeline_version],
                image=image,
                volume_mounts=[client.V1VolumeMount(
                    mount_path='/data',
                    name='pv'
                )]
            )
        ]),
        volumes=[client.V1Volume(
            name='pv',
            persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                claim_name='retrainer-pvc',
            )
        )]
    )

    deployment = client.V1Deployment(
        metadata=client.V1ObjectMeta(
            namespace=namespace,
            name=deployment_name
        ),
        spec=client.V1DeploymentSpec(
            selector=client.V1LabelSelector(
                match_labels={'app': pod_name}
            ),
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    namespace=namespace,
                    name=pod_name,
                    labels={'app': pod_name}
                ),
                spec=pod
            )
        )
    )

    try:
        apps_api.patch_namespaced_deployment(
            name=deployment_name,
            namespace=namespace,
            body=deployment
        )
    except client.ApiException:
        apps_api.create_namespaced_deployment(
            namespace=namespace,
            body=deployment
        )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str)
    parser.add_argument('--pipeline_version', type=str)
    args = parser.parse_args()

    deploy(args.image, args.pipeline_version)
