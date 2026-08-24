from import_export import resources
from .models import Student
from academics.models import ClassRoom

class StudentResource(resources.ModelResource):
    class Meta:
        model = Student
        import_id_fields = ['admission_number']  # update if exists, else create
        skip_unchanged = True
        report_skipped = True
        fields = (
            'admission_number',
            'first_name',
            'middle_name',          # <-- ADDED
            'last_name',
            'date_of_birth',
            'gender',
            'class_room__level',    # use level id like 1, 2, 3
            'class_room__stream',   # use A, B, C
            'guardian',
            'phone_number',
            'status'
        )
        export_order = fields  # keep export same order as import

    def before_import_row(self, row, **kwargs):
        # Convert class name like "1 A" to ClassRoom ID
        level = row.get('class_room__level')
        stream = row.get('class_room__stream')
        if level and stream:
            class_room = ClassRoom.objects.filter(level=level, stream=stream).first()
            if class_room:
                row['class_room'] = class_room.id
            else:
                raise ValueError(f"ClassRoom level={level} stream={stream} does not exist. Create it first in Academics.")