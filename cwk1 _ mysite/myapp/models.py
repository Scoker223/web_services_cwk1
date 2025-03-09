from django.db import models
from django.contrib.auth.models import User


class Professor(models.Model):
    id = models.CharField(max_length=10, primary_key=True, unique=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.name} ({self.id})"

class Module(models.Model):
    code = models.CharField(max_length=10, primary_key=True, unique=True)
    module_name = models.CharField(max_length=30)

    def __str__(self):
        return f"{self.module_name} ({self.code})"

class ModuleInstance(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='instances')
    year = models.IntegerField()
    semester = models.IntegerField()
    professors = models.ManyToManyField(Professor, related_name='module_instances')
    
    def __str__(self):
        return f"{self.module.module_name} ({self.year} - Semester {self.semester})"

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    professor = models.ForeignKey(Professor, on_delete=models.CASCADE)
    module_instance = models.ForeignKey(ModuleInstance, on_delete=models.CASCADE)
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # Rating between 1 to 5

    class Meta:
        unique_together = ('user', 'professor', 'module_instance')

    def __str__(self):
        return f"{self.user.username} rated {self.professor.name} ({self.rating} stars) for {self.module_instance.module.code}"