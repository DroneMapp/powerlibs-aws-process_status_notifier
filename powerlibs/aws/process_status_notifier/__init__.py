from cached_property import cached_property

from powerlibs.aws.sqs.publisher import SQSPublisher


class ProcessStatusNotifier:

    def __init__(self, queue_name, process_name, topics_format='{process_name}__{status}', payload=None):
        self.process_name = process_name
        self.payload = payload if payload else dict()
        self.queue_name = queue_name
        self._load_basic_topics(topics_format)

    @cached_property
    def notifier(self):
        return SQSPublisher()

    def _load_basic_topics(self, topics_format):
        stati = 'started', 'finished', 'failed'
        self.status_topics = {
            status: [topics_format.format(
                process_name=self.process_name,
                status=status
            )] for status in stati
        }

    def __repr__(self):
        return '<Process Status Notifier for {}>'.format(self.process_name)

    def __enter__(self, *args):
        self.notify('started')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type:
            self.notify('failed', payload={**self.payload, 'message': str(exc_value)})
        else:
            self.notify('finished')

    def notify(self, status, payload=None):
        topics = self.status_topics[status]
        payload = payload if payload else self.payload
        for topic in topics:
            self.notifier.publish(self.queue_name, payload, attributes={'topic': topic})
