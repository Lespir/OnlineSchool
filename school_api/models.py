from django.db import models

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import Http404


class Author(models.Model):
    name = models.CharField('Name', max_length=128)
    surname = models.CharField('Surname', max_length=128)
    patronymic = models.CharField('Patronymic', max_length=128, null=True, blank=True)

    class Meta:
        verbose_name = 'Автор'
        verbose_name_plural = 'Авторы'

    def __str__(self):
        return f"{self.surname} {self.name}"


class Student(models.Model):
    name = models.CharField('Name', max_length=128)
    surname = models.CharField('Surname', max_length=128)
    patronymic = models.CharField('Patronymic', max_length=128, null=True, blank=True)

    class Meta:
        verbose_name = 'Студент'
        verbose_name_plural = 'Студенты'

    def __str__(self):
        return f"{self.surname} {self.name}"


class Product(models.Model):
    name = models.CharField('Product Name', max_length=1024)
    author = models.ForeignKey('Author', on_delete=models.CASCADE, verbose_name='author')
    start_date = models.DateTimeField('Product start date')
    price = models.DecimalField("Product price", max_digits=9, decimal_places=2)
    min_students = models.IntegerField('Minimum numbers of students in a group', default=10)
    max_students = models.IntegerField('Maximum numbers of students in a group', default=30)

    class Meta:
        verbose_name = 'Продукт'
        verbose_name_plural = 'Продукты'

    @property
    def price_display(self):
        return f"{self.price} rub"

    def __str__(self):
        return self.name


class ProductAccess(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='product')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, verbose_name='student')
    access = models.BooleanField('Access', default=True)

    class Meta:
        verbose_name = 'Доступ к продукту'

    def __str__(self):
        return f"{self.student} - {self.product}"


class Lesson(models.Model):
    name = models.CharField('Lesson name', max_length=1024)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, verbose_name='product')
    video = models.URLField(max_length=256)

    def __str__(self):
        return self.name


class Group(models.Model):
    name = models.CharField('Group name', max_length=512)
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    students = models.ManyToManyField('Student', verbose_name='list of students')

    def __str__(self):
        return f"{self.name} - {self.product}"


@receiver(post_save, sender=ProductAccess)
def distribute_student(sender, instance, **kwargs):
    if instance.access:
        product = instance.product
        student = instance.student

        min_students = product.min_students
        max_students = product.max_students

        total_students = Group.objects.filter(product_id=product).aggregate(
            total_students=models.Sum('students__count'))['total_students']

        not_empty_groups = Group.objects.filter(product=product, students__isnull=False)

        min_students_group = Group.objects.filter(product=product).annotate(
            num_students=models.Count('students')).order_by('num_students').first()

        min_not_empty_group = Group.objects.filter(product=product, students__isnull=False).annotate(
            num_students=models.Count('students')).order_by('num_students').first()

        if min_students_group.students.count() != max_students:
            if not not_empty_groups:
                min_students_group.students.add(student)
            else:
                if total_students + 1 // min_students > not_empty_groups.count():
                    students_per_group = total_students + 1 // (not_empty_groups.count() + 1)
                    groups = Group.objects.filter(product=product)
                    all_students = [student]

                    for group in groups:
                        students = group.students.all()
                        all_students.extend(students)

                    for group in groups:
                        group.students.clear()

                    needed_groups = not_empty_groups.count() + 1
                    ref_groups = groups if needed_groups == groups.count() else groups[:needed_groups]

                    for i in range(needed_groups):
                        ref_groups[i].students.add(*all_students[students_per_group * i:students_per_group * (i + 1)])

                else:
                    min_not_empty_group.students.add(student)
        else:
            raise Http404('All groups are filled')
