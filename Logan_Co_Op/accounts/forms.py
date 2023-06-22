import profile
from django import forms
from .models import Account,UserProfile

class RegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Enter Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder':'Confirm Password'}))
    class Meta:
        model = Account
        fields = ['first_name','last_name','phone_number','email','password']
    def __init__(self,*args,**kwargs):
        super(RegistrationForm, self).__init__(*args,**kwargs)
        self.fields['first_name'].widget.attrs['placeholder']="Enter First Name"
        self.fields['last_name'].widget.attrs['placeholder']="Enter Last Name"
        self.fields['phone_number'].widget.attrs['placeholder']="Enter Phone Number"
        self.fields['email'].widget.attrs['placeholder']="Enter Email Address"
        for field in self.fields:
            self.fields[field].widget.attrs['class']="form-control"
    def clean(self): # super keyword is used to change the way the class is saved
        cleaned_data = super(RegistrationForm,self).clean()
        password=cleaned_data.get('password')
        confirm_password=cleaned_data.get('confirm_password')

        if password != confirm_password:
            raise forms.ValidationError(
                "Try to remember your password man, fgs! and try to avoid typos dude, eww."
            )

class UserForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ('first_name','last_name','phone_number')
    def __init__(self,*args,**kwargs):
        super(UserForm, self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class']="form-control"

class UserProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, error_messages={'invalid':("Image Files Only")}, widget=forms.FileInput)
    class Meta:
        model = UserProfile
        fields = ('profile_picture', 'address_line_1','address_line_2','city','state','country',)
    def __init__(self,*args,**kwargs):
        super(UserProfileForm, self).__init__(*args,**kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class']="form-control"

