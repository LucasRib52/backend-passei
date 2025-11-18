from rest_framework import serializers
import re
from .models import Course, Module, Lesson, Category
from professors.serializers import ProfessorSerializer
from professors.models import Professor
from django.utils.text import slugify
from themembers.models import TheMembersProduct, TheMembersIntegration
import json


class CategorySerializer(serializers.ModelSerializer):
    # Torna o slug opcional para permitir geração automática
    slug = serializers.CharField(required=False, allow_blank=True)
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
    
    def get_courses_count(self, obj):
        return obj.course_set.count()
    
    def create(self, validated_data):
        # Gerar slug automaticamente se não fornecido
        if 'slug' not in validated_data or not validated_data['slug']:
            validated_data['slug'] = slugify(validated_data['name'])
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Gerar slug automaticamente se nome foi alterado
        if 'name' in validated_data and validated_data['name'] != instance.name:
            validated_data['slug'] = slugify(validated_data['name'])
        return super().update(instance, validated_data)


class CategoryPublicSerializer(serializers.ModelSerializer):
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'slug', 'color', 'icon', 'is_active', 'courses_count']
    
    def get_courses_count(self, obj):
        return obj.course_set.count()


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = '__all__'


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    
    class Meta:
        model = Module
        fields = '__all__'


class CourseSerializer(serializers.ModelSerializer):
    professor = ProfessorSerializer(read_only=True)
    professors = ProfessorSerializer(many=True, read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    category = CategoryPublicSerializer(read_only=True)
    categories = CategoryPublicSerializer(many=True, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    themembers_product_ids = serializers.SerializerMethodField()
    # Expor flags de pagamento
    allow_pix = serializers.BooleanField(read_only=True)
    allow_credit_card = serializers.BooleanField(read_only=True)
    allow_bank_slip = serializers.BooleanField(read_only=True)
    allow_boleto_installments = serializers.BooleanField(read_only=True)
    max_boleto_installments = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Course
        fields = '__all__'

    def get_themembers_product_ids(self, obj):
        return obj.get_themembers_product_ids()


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    # Novo campo de conteúdo programático do curso (opcional)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True, help_text='Conteúdo do curso')
    # Tratar course_image como arquivo de imagem
    course_image = serializers.ImageField(required=False, allow_null=True, help_text='Imagem do curso')
    # Vídeo do curso
    course_video = serializers.FileField(required=False, allow_null=True, help_text='Vídeo do curso')
    # Link do grupo do WhatsApp
    whatsapp_group_link = serializers.URLField(required=False, allow_blank=True, allow_null=True, help_text='Link para o grupo do WhatsApp do curso')
    """
    Serializer para criação e atualização de cursos
    Permite definir o professor por ID
    """
    professor = serializers.PrimaryKeyRelatedField(
        queryset=Professor.objects.all(),
        required=True
    )
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        allow_null=True
    )
    # Novos campos M2M (aceitam JSON ou string JSON via multipart)
    professors = serializers.JSONField(required=False, write_only=True)
    categories = serializers.JSONField(required=False, write_only=True)
    themembers_product_ids = serializers.JSONField(required=False, write_only=True, help_text='Lista de IDs de produtos TheMembers (máximo 10)')
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    # Flags de pagamento (admin pode editar)
    allow_pix = serializers.BooleanField(required=False)
    allow_credit_card = serializers.BooleanField(required=False)
    allow_bank_slip = serializers.BooleanField(required=False)
    allow_boleto_installments = serializers.BooleanField(required=False)
    max_boleto_installments = serializers.IntegerField(required=False)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'detailed_description', 'content',
            'price', 'original_price', 'duration', 'students_count',
            'rating', 'reviews_count', 'professor', 'category',
            'benefits', 'requirements', 'status', 'created_at',
            'course_image', 'course_video', 'video_url', 'is_bestseller', 'is_complete', 'is_new', 'is_featured',
            'themembers_product_id', 'whatsapp_group_link',
            # Pagamentos
            'allow_pix', 'allow_credit_card', 'allow_bank_slip', 'allow_boleto_installments', 'max_boleto_installments',
            # Campos auxiliares (write_only) para entrada via multipart/JSON
            'professors', 'categories', 'themembers_product_ids'
        ]
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    # --- Validações de campo ---
    def validate_title(self, value: str):
        """
        O Asaas não aceita emojis na descrição/título que enviamos.
        Bloqueamos aqui para evitar erro no checkout.
        """
        if not value:
            return value
        emoji_pattern = re.compile(
            "["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U0001F900-\U0001F9FF"  # supplemental symbols
            u"\U0001FA70-\U0001FAFF"  # symbols extended-A
            u"\u2600-\u26FF"          # misc symbols
            u"\u2700-\u27BF"          # dingbats
            "]+",
            flags=re.UNICODE,
        )
        if emoji_pattern.search(value):
            raise serializers.ValidationError("Título não pode conter emoji. Remova símbolos/emoji do título.")
        return value

    def _parse_list_field(self, value):
        """Aceita lista, JSON string ou string separada por vírgula."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            v = value.strip()
            if not v:
                return []
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            # fallback csv
            return [s.strip() for s in v.split(',') if s.strip()]
        return []

    def create(self, validated_data):
        request_data = self.initial_data
        professors_ids = self._parse_list_field(request_data.get('professors'))
        categories_ids = self._parse_list_field(request_data.get('categories'))
        tm_product_ids = self._parse_list_field(request_data.get('themembers_product_ids'))

        # Compat: define principal com base no primeiro da lista
        if professors_ids and not validated_data.get('professor'):
            try:
                validated_data['professor'] = Professor.objects.get(id=int(professors_ids[0]))
            except Exception:
                pass
        if categories_ids and not validated_data.get('category'):
            try:
                validated_data['category'] = Category.objects.get(id=int(categories_ids[0]))
            except Exception:
                pass

        # Remover campos auxiliares que não pertencem ao modelo antes de criar
        validated_data.pop('professors', None)
        validated_data.pop('categories', None)
        validated_data.pop('themembers_product_ids', None)

        course = super().create(validated_data)

        # M2M: Professores
        if professors_ids:
            prof_objs = Professor.objects.filter(id__in=[int(i) for i in professors_ids])
            course.professors.set(prof_objs)
        # M2M: Categorias
        if categories_ids:
            cat_objs = Category.objects.filter(id__in=[int(i) for i in categories_ids])
            course.categories.set(cat_objs)
        # M2M: TheMembers products (e campo legado)
        if tm_product_ids:
            # Mantém o primeiro no campo legado
            first_pid = str(tm_product_ids[0])
            course.themembers_product_id = first_pid
            course.save(update_fields=['themembers_product_id'])
            # Vincula todos via integração
            provided_ids = [str(i) for i in tm_product_ids]
            products = list(TheMembersProduct.objects.filter(product_id__in=provided_ids))
            existing_ids = {p.product_id for p in products}
            missing_ids = [pid for pid in provided_ids if pid not in existing_ids]
            # Cria placeholders para produtos não sincronizados ainda
            for mid in missing_ids:
                try:
                    p = TheMembersProduct.objects.create(
                        product_id=mid,
                        title=mid,
                        description='',
                        price=0,
                        image_url='',
                        status='active'
                    )
                    products.append(p)
                except Exception:
                    pass
            for product in products:
                TheMembersIntegration.objects.update_or_create(
                    course=course, product=product, defaults={'status': 'active'}
                )

        return course

    def update(self, instance, validated_data):
        request_data = self.initial_data
        professors_ids = self._parse_list_field(request_data.get('professors'))
        categories_ids = self._parse_list_field(request_data.get('categories'))
        tm_product_ids = self._parse_list_field(request_data.get('themembers_product_ids'))

        # Remover campos auxiliares antes de atualizar
        validated_data.pop('professors', None)
        validated_data.pop('categories', None)
        validated_data.pop('themembers_product_ids', None)

        instance = super().update(instance, validated_data)

        # M2M: Professores
        if professors_ids is not None:
            prof_objs = Professor.objects.filter(id__in=[int(i) for i in professors_ids])
            instance.professors.set(prof_objs)
            # Compat: define principal se fornecido
            if professors_ids:
                try:
                    instance.professor = Professor.objects.get(id=int(professors_ids[0]))
                except Exception:
                    pass
        # M2M: Categorias
        if categories_ids is not None:
            cat_objs = Category.objects.filter(id__in=[int(i) for i in categories_ids])
            instance.categories.set(cat_objs)
            if categories_ids:
                try:
                    instance.category = Category.objects.get(id=int(categories_ids[0]))
                except Exception:
                    pass
        # M2M: TheMembers products
        if tm_product_ids is not None:
            # Atualiza campo legado com o primeiro
            first_pid = str(tm_product_ids[0]) if tm_product_ids else None
            instance.themembers_product_id = first_pid
            instance.save(update_fields=['themembers_product_id'])
            # Atualiza integrações: ativa as fornecidas e mantém outras existentes se não fornecido? Aqui substitui
            if tm_product_ids:
                provided_ids = [str(i) for i in tm_product_ids]
                products_qs = TheMembersProduct.objects.filter(product_id__in=provided_ids)
                products = list(products_qs)
                existing_ids = {p.product_id for p in products}
                missing_ids = [pid for pid in provided_ids if pid not in existing_ids]
                for mid in missing_ids:
                    try:
                        p = TheMembersProduct.objects.create(
                            product_id=mid,
                            title=mid,
                            description='',
                            price=0,
                            image_url='',
                            status='active'
                        )
                        products.append(p)
                    except Exception:
                        pass
                # Limpa integrações antigas não listadas
                TheMembersIntegration.objects.filter(course=instance).exclude(product__product_id__in=provided_ids).delete()
                for product in products:
                    TheMembersIntegration.objects.update_or_create(
                        course=instance, product=product, defaults={'status': 'active'}
                    )
            else:
                # Se lista vazia, remove integrações
                TheMembersIntegration.objects.filter(course=instance).delete()

        return instance


class CourseListSerializer(serializers.ModelSerializer):
    professor_name = serializers.CharField(source='professor.name', read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'price', 'original_price',
            'duration', 'students_count', 'rating', 'reviews_count',
            'professor_name', 'status', 'created_at', 'course_image'
        ]


class CoursePublicListSerializer(serializers.ModelSerializer):
    """
    Serializer para listagem pública de cursos
    Inclui o professor completo para o frontend
    """
    professor = ProfessorSerializer(read_only=True)
    professors = ProfessorSerializer(many=True, read_only=True)
    category = CategoryPublicSerializer(read_only=True)
    categories = CategoryPublicSerializer(many=True, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    themembers_product_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'detailed_description', 'price', 'original_price',
            'duration', 'students_count', 'rating', 'reviews_count',
            'professor', 'professors', 'category', 'categories', 'benefits', 'requirements', 'status', 'created_at',
            'course_image', 'course_video', 'video_url', 'is_bestseller', 'is_complete', 'is_new', 'is_featured', 'themembers_product_ids',
            # Expor flags
            'allow_pix', 'allow_credit_card', 'allow_bank_slip', 'allow_boleto_installments', 'max_boleto_installments'
        ]

    def get_themembers_product_ids(self, obj):
        return obj.get_themembers_product_ids()


class CourseDetailSerializer(serializers.ModelSerializer):
    professor = ProfessorSerializer(read_only=True)
    modules = ModuleSerializer(many=True, read_only=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)


class ModulePublicSerializer(serializers.ModelSerializer):
    """Serializer público de Módulo com lista de tópicos"""
    lessons = LessonSerializer(many=True, read_only=True)
    topics_list = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = ['id', 'title', 'lessons_count', 'duration', 'order', 'topics_list']

    def get_topics_list(self, obj):
        if obj.topics:
            return [t.strip() for t in obj.topics.split(',')]
        return []

class CoursePublicDetailSerializer(serializers.ModelSerializer):
    """Serializer público de detalhes de curso"""
    professor = ProfessorSerializer(read_only=True)
    professors = ProfessorSerializer(many=True, read_only=True)
    modules = ModulePublicSerializer(many=True, read_only=True)
    category = CategoryPublicSerializer(read_only=True)
    categories = CategoryPublicSerializer(many=True, read_only=True)
    benefits_list = serializers.SerializerMethodField()
    requirements_list = serializers.SerializerMethodField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)
    themembers_product_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'description', 'detailed_description', 'content',
            'price', 'original_price', 'duration', 'students_count',
            'rating', 'reviews_count', 'professor', 'professors', 'category', 'categories',
            'benefits_list', 'requirements_list',
            'modules', 'course_image', 'course_video', 'video_url', 'status', 'created_at',
            'is_bestseller', 'is_complete', 'is_new', 'is_featured', 'themembers_product_ids',
            # Expor flags
            'allow_pix', 'allow_credit_card', 'allow_bank_slip', 'allow_boleto_installments', 'max_boleto_installments'
        ]

    def get_benefits_list(self, obj):
        if obj.benefits:
            return [b.strip() for b in obj.benefits.split(',')]
        return []

    def get_requirements_list(self, obj):
        if obj.requirements:
            return [r.strip() for r in obj.requirements.split(',')]
        return [] 

    def get_themembers_product_ids(self, obj):
        return obj.get_themembers_product_ids()


class ModuleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer para criação/atualização de módulos (admin)"""
    class Meta:
        model = Module
        fields = ['id','title','description','lessons_count','duration','order','topics','course'] 