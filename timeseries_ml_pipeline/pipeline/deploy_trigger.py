from kubernetes import client, config
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config.load_incluster_config()


def deploy(image: str):
    job_namespace = 'retraining-job'
    job_name = 'test-job'

    batch_api = client.BatchV1Api()

    job_pod = client.V1PodSpec(
        restart_policy='Never',
        containers=([
            client.V1Container(
                name='retraining-job',
                command=['python3'],
                args=['-m', 'training.retraining_trigger'],
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
                claim_name='retraining-pvc',
            )
        )]
    )

    cron_schedule = '*/1 * * * *'
    job = client.V1CronJob(
        metadata=client.V1ObjectMeta(
            name=job_name,
            namespace=job_namespace
        ),
        spec=client.V1CronJobSpec(
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(
                    template=client.V1PodTemplateSpec(
                        spec=job_pod
                    )
                )
            ),
            schedule=cron_schedule,
            successful_jobs_history_limit=3
        )
    )

    try:
        batch_api.patch_namespaced_cron_job(
            name=job_name,
            namespace=job_namespace,
            body=job
        )
    except client.ApiException:
        batch_api.create_namespaced_cron_job(namespace=job_namespace, body=job)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', type=str)
    args = parser.parse_args()

    deploy(image=args.image)
