from tortoise import fields, models


class PDDetectionResult(models.Model):
    id = fields.IntField(pk=True)
    file_name = fields.CharField(max_length=255, null=False)
    model_path = fields.CharField(max_length=1024, null=True)
    overall_prediction = fields.CharField(max_length=16, null=True)
    confidence = fields.FloatField(null=True)
    average_probability = fields.FloatField(null=True)
    total_epochs = fields.IntField(null=True)
    on_epochs = fields.IntField(null=True)
    off_epochs = fields.IntField(null=True)
    epoch_predictions = fields.JSONField(null=True)
    epoch_probabilities = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "pd_detection_results"
